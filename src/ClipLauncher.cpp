#include "ClipLauncher.h"
#include "Clip.h"
#include "Voice.h"
#include "Util.h"

#include <SDL.h>

#include <algorithm>
#include <iostream>
#include <chrono>

// Helper to check validity of audio specs
bool operator==( const SDL_AudioSpec& a, const SDL_AudioSpec& b )
{
	return ( a.freq		== b.freq &&
			 a.format	== b.format &&
			 a.channels == b.channels &&
			 a.samples	== b.samples);
}
bool operator!=( const SDL_AudioSpec& a, const SDL_AudioSpec& b )
{
	return !(a == b);
}

ClipLauncher::ClipLauncher() :
	m_bPlaying( false ),
	m_uMaxSampleCount( 0 ),
	m_uNumBufsCompleted( 0 ),
	m_uSamplePos( 0 )
{}

// Initialize the sound manager's audio spec
bool ClipLauncher::Init( SDL_AudioSpec * pAudioSpec )
{
	// Get out if invalid
	if ( pAudioSpec == nullptr )
		return false;

	// For now we're only doing mono float
	if ( pAudioSpec->format != AUDIO_F32 || pAudioSpec->channels != 1 )
		return false;

	// Assign the audio spec and set up the pull callback
	m_pAudioSpec.reset( new SDL_AudioSpec( *pAudioSpec ) );
	m_pAudioSpec->callback = (SDL_AudioCallback) ClipLauncher::FillAudio;
	m_pAudioSpec->userdata = this;

	// Try and open the audio spec and check its validity
	SDL_AudioSpec received{ 0 };
	if ( SDL_OpenAudio( m_pAudioSpec.get(), &received ) != 0 )
	{
		std::cout << "Error initializing SDL Audio" << std::endl;
		std::cout << SDL_GetError() << std::endl;
		m_pAudioSpec.reset();
		return false;
	}
	// If we got it, check the validity
	else if ( *m_pAudioSpec != received )
	{
		// if bad, reset, close audio, return false
		m_pAudioSpec.reset();
		SDL_CloseAudio();
		return false;
	}

	// We don't start off as playing
	m_bPlaying = false;

	return true;
}

ClipLauncher::~ClipLauncher()
{
	if ( m_pAudioSpec && this == m_pAudioSpec->userdata )
	{
		SDL_CloseAudio();
	}
}

// Register a clip with the SoundManager so it can be recalled later as a voice. A clip can contain a
// head file, tail file, and a sample count for the fade (fade up from zero, fade out to next loop, etc.) 
bool ClipLauncher::RegisterClip( std::string strClipName, std::string strHeadFile, std::string strTailFile, size_t uFadeDurationMS )
{
	// We need to know what format the streaming code expects in order to load
	// that kind of data, so if this isn't ready then get out
	if ( m_pAudioSpec == nullptr || m_pAudioSpec->userdata != this )
		return false;

	// Because the audio thread walks the map we're about to add something to, we
	// don't allow registering clips while the audio is playing
	if ( m_bPlaying )
	{
		std::cerr << "Error: Attempting to register clip " << strClipName << " with playing SoundManager!" << std::endl;
		return false;
	}

	// If we already have this clip stored, return true
	// (I should make a way of unregistering, or allowing overwrites)
	if ( m_mapClips.find( strClipName ) != m_mapClips.end() )
		return true;

	// This will get filled in if we load successfully
	float * pSoundBuffer( nullptr );	// Buffer of head samples
	Uint32 uNumBytesInHead( 0 );		// number of head samples
	float * pTailBuffer( nullptr );		// Buffer of tail samples
	Uint32 uNumBytesInTail( 0 );		// number of tail samples

	// Load the head file, check against our spec
	SDL_AudioSpec wavSpec{ 0 };
	if ( SDL_LoadWAV( strHeadFile.c_str(), &wavSpec, (Uint8 **) &pSoundBuffer, &uNumBytesInHead ) )
	{
		if ( wavSpec == *m_pAudioSpec )
		{
			// Load the tail file, check against our spec
			if ( SDL_LoadWAV( strTailFile.c_str(), &wavSpec, (Uint8 **) &pTailBuffer, &uNumBytesInTail ) )
			{
				if ( wavSpec != *m_pAudioSpec )
				{
					// It's ok if this fails, just free and zero these guys
					if ( pTailBuffer)
						SDL_FreeWAV( (Uint8 *) pTailBuffer );
					pTailBuffer = nullptr;
					uNumBytesInTail = 0;
				}
			}

			// Construct the clip
			const size_t uNumSamplesInHead = uNumBytesInHead / sizeof( float );
			const size_t uNumSamplesInTail = uNumBytesInTail / sizeof( float );
			const size_t uFadeDurationSamples = (size_t) (uFadeDurationMS *(m_pAudioSpec->freq / 1000.f));
			m_uMaxSampleCount = std::max( m_uMaxSampleCount, uNumSamplesInHead );
			m_mapClips[strClipName] = Clip( strClipName, pSoundBuffer, uNumSamplesInHead, pTailBuffer, uNumSamplesInTail, uFadeDurationSamples );
			return true;
		}
		else
		{
			// If we got an invalid audio spec but were able to load the data,
			// we have to free the buffer before getting out (or we leak)
			if ( pSoundBuffer )
				SDL_FreeWAV( (Uint8 *) pSoundBuffer );
		}
	}

	return false;
}

// Called by main thread, locks mutex
void ClipLauncher::getMessagesFromAudThread()
{
	// We gotta lock this while we mess with the public queue
	std::lock_guard<std::mutex> lg( m_muAudioMutex );

	// Get out if empty
	if ( m_liPublicCmdQueue.empty() )
		return;

	// Grab the front, maybe inc buf count and pop
	Command tFront = m_liPublicCmdQueue.front();
	if ( tFront.eID == ECommandID::BufCompleted )
	{
		m_liPublicCmdQueue.pop_front();
		m_uNumBufsCompleted += tFront.uData;
	}

	if ( std::any_of( m_liPublicCmdQueue.begin(), m_liPublicCmdQueue.end(), [] ( const Command& cmd ) { return cmd.eID == ECommandID::AllQuiet; } ) )
	{
		m_liPublicCmdQueue.clear();
		SetPlayPause( false );
	}
}

// Called by client thread
void ClipLauncher::Update()
{
	// Just see if the audio thread has 
	// left any tasks for us to deal with 
	getMessagesFromAudThread();
}

bool ClipLauncher::HandleCommand( Command cmd )
{
	if ( cmd.eID == ECommandID::None )
		return false;

	if ( cmd.eID == ECommandID::StartVoice && m_bPlaying == false )
		cmd.uData = 0;

	std::lock_guard<std::mutex> lg( m_muAudioMutex );
	m_liPublicCmdQueue.push_back( cmd );

	return true;
}

// Adds several message-wrapped tasks to the queue (locks mutex once)
bool ClipLauncher::HandleCommands( std::list<Command> liCommands )
{
	if ( liCommands.empty() )
		return false;

	for ( Command& cmd : liCommands)
		if ( cmd.eID == ECommandID::StartVoice && m_bPlaying == false )
			cmd.uData = 0;

	std::lock_guard<std::mutex> lg( m_muAudioMutex );
	m_liPublicCmdQueue.splice( m_liPublicCmdQueue.end(), liCommands );

	return true;
}

void ClipLauncher::SetPlayPause( bool bPlayPause )
{
	// This gets set if Init is successful
	if ( m_pAudioSpec->userdata == this )
	{
		// Toggle audio playback (and bool)
		m_bPlaying = bPlayPause;

		if ( m_bPlaying )
			SDL_PauseAudio( 0 );
		else
			SDL_PauseAudio( 1 );
	}
}

bool ClipLauncher::GetPlayPause() const
{
	return m_bPlaying;
}

size_t ClipLauncher::GetSampleRate() const
{
	return m_pAudioSpec ? m_pAudioSpec->freq : 0;
}

size_t ClipLauncher::GetBufferSize() const
{
	return m_pAudioSpec ? m_pAudioSpec->samples : 0;
}

size_t ClipLauncher::GetMaxSampleCount() const
{
	return m_uMaxSampleCount;
}

size_t ClipLauncher::GetNumBufsCompleted() const
{
	return m_uNumBufsCompleted;
}

size_t ClipLauncher::GetNumSamplesInClip( std::string strClipName, bool bTail /*= false*/ ) const
{
	auto it = m_mapClips.find( strClipName );
	if ( it != m_mapClips.end() )
		return it->second.GetNumSamples( bTail );
	return 0;
}

SDL_AudioSpec * ClipLauncher::GetAudioSpecPtr() const
{
	return m_pAudioSpec.get();
}

Clip * ClipLauncher::GetClip( std::string strClipName ) const
{
	auto itClip = m_mapClips.find( strClipName );
	if ( itClip != m_mapClips.end() )
		return (Clip *) &itClip->second;
	return nullptr;
}

// Audio thread functions start here
////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Static SDL audio callback function
// (each instance sets its own userdata to this, 
// so I guess multiple instances are legit)
/*static*/ void ClipLauncher::FillAudio( void * pUserData, uint8_t * pStream, int nSamplesDesired )
{
	// livin on a prayer
	((ClipLauncher *) pUserData)->fill_audio_impl( pStream, nSamplesDesired );
}

// Called via the static fill_audi function
void ClipLauncher::fill_audio_impl( uint8_t * pStream, int nBytesToFill )
{
	// Don't do nothin if they gave us nothin
	if ( pStream == nullptr || nBytesToFill == 0 )
		return;

	// Silence no matter what
	memset( pStream, 0, nBytesToFill );

	// Get tasks from public thread and handle them
	// Also let them know a buffer is about to complete
	Command cmdBufCompleted;
	cmdBufCompleted.eID = ECommandID::BufCompleted;
	cmdBufCompleted.uData = 1;
	getMessagesFromMainThread( { cmdBufCompleted } );

	// Nothing to do
	if ( m_liVoices.empty() )
		return;

	// The number of float samples we want
	const size_t uNumSamplesDesired = nBytesToFill / sizeof( float );

	// Fill audio data for each loop
	for ( Voice& v : m_liVoices )
		v.RenderData( (float *) pStream, uNumSamplesDesired, m_uSamplePos );

	// Update sample counter, reset if we went over
	m_uSamplePos += uNumSamplesDesired;
	if ( m_uSamplePos > m_uMaxSampleCount )
	{
		// Just do a mod
		m_uSamplePos %= m_uMaxSampleCount;
	}
}

// Called by audio thread, locks mutex while getting client tasks
void ClipLauncher::getMessagesFromMainThread( std::list<Command> liCommandsToPost )
{
	// Lock the mutex, and take any tasks the client
	// thread has left us and put them into our queue
	{
		std::lock_guard<std::mutex> lg( m_muAudioMutex );

		// See if there's anything still in the public queue
		if ( m_liPublicCmdQueue.empty() == false )
		{
			// If so, we need to potentially merge any BufCompleted tasks
			// into a single task (with one buffer count) for the client thread
			if ( m_liPublicCmdQueue.front().eID == ECommandID::BufCompleted )
			{
				if ( liCommandsToPost.front().eID == ECommandID::BufCompleted )
				{
					// If we need to merge, add liCommandsToPost count to the
					// public queue's count and pop the task from liCommandsToPost
					m_liPublicCmdQueue.front().uData += liCommandsToPost.front().uData;
					liCommandsToPost.pop_front();
				}
			}

			// Take all other tasks posted by client thread, tack to end of m_liAudioCmdQueue
			m_liAudioCmdQueue.splice( m_liAudioCmdQueue.end(), m_liPublicCmdQueue );
		}

		// The public queue is now empty; make it the new list
		m_liPublicCmdQueue = std::move( liCommandsToPost );
	}

	// Remove any voices that have stopped playing
	m_liVoices.remove_if( [] ( const Voice& v ) { return v.GetState() == Voice::EState::Stopped; } );

	// Handle each task in m_liAudioCmdQueue
	for ( Command cmd : m_liAudioCmdQueue )
	{
		// Find the voice associated with the command's ID - this is dumb, but easy
		struct prFindVoice
		{
			const Command * pCmd;
			prFindVoice( const Command& cmd ) : pCmd( &cmd ) {};
			bool operator()(const Voice& v) { return v.GetID() == pCmd->iData; };
		};
		auto itVoice = std::find_if( m_liVoices.begin(), m_liVoices.end(), prFindVoice( cmd ) );

		// No need for the start command - it's better
		// (and thread safe) to start each clip individually

		// Handle the command
		switch ( cmd.eID )
		{
			// Stop every loop active voice
			case ECommandID::StopVoices:
				for ( Voice& v : m_liVoices )
					v.SetStopping( cmd.uData );
				break;

			// Create a voice for a specific clip
			case ECommandID::StartVoice:
			case ECommandID::OneShot:
				// If it isn't already there, construct the voice
				if ( itVoice == m_liVoices.end() )
					m_liVoices.emplace_back( cmd );
				// Otherwise try set the voice to pending, which 
				// will either queue to play or leave it alone
				else
					itVoice->SetPending( cmd.uData, cmd.eID == ECommandID::StartVoice );
				break;

			// Stop a specific playing voice
			case ECommandID::StopVoice:
				if ( itVoice != m_liVoices.end() )
					itVoice->SetStopping( cmd.uData );
				break;

			// Set the volume of a playing voice
			case ECommandID::SetVolume:
				if ( itVoice != m_liVoices.end() )
					itVoice->SetVolume( cmd.fData );
				break;

			// That's all we handle here
			default:
				break;
		}
	}

	// The audio thread doesn't care about anything else
	// so clear the list when we're done with it
	m_liAudioCmdQueue.clear();

	// If we have no voices, post a message indicating so
	if ( m_liVoices.empty() )
	{
		std::lock_guard<std::mutex> lg( m_muAudioMutex );
		ClipLauncher::Command cmd;
		cmd.eID = ClipLauncher::ECommandID::AllQuiet;
		m_liPublicCmdQueue.push_back( cmd );
	}
}