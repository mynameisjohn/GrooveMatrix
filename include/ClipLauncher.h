#pragma once

#include <string>
#include <map>
#include <list>
#include <mutex>
#include <memory>
#include <stdint.h>

// Forwards for clip, voice
class Clip;
class Voice;

// Forward for SDL audio spec
struct SDL_AudioSpec;

/***********************************************
ClipLauncher class - manages clip playback

This class owns a number of audio clips that can
be rendered to an SDL mix buffer by instantiating
voices corresponding to the clips. 

Clip playback is controlled via a command pattern
that allows clients to control when a clip starts
and stops as well as whether or not the clip loops

This class is the one that actually receives SDL's
FillAudio callback, which is delegated to active
voices. Because that function is called on an 
SDL audio thread, this class owns a mutex that
locks data that could be used by both threads. 

For example, the commands that control playback
are stored in a queue, and this queue is accessed
by both clients and the audio thread. 
***********************************************/

class ClipLauncher
{
public:
	// Default Constructor initializes variables
	ClipLauncher();

	// Init function actually starts SDL audio
	// using provided audio spec (if valid)
	bool Init( SDL_AudioSpec * pAudioSpec );

	// Destructor tears down SDL Audio if it was started
	~ClipLauncher();

	// Called periodically to pick up messages posted by aud thread
	void Update();

	// Play / Pause the audio device
	bool GetPlayPause() const;
	void SetPlayPause( bool bPlayPause );

	// Various gets
	size_t GetMaxSampleCount() const;
	size_t GetSampleRate() const;
	size_t GetBufferSize() const;
	size_t GetNumBufsCompleted() const;
	size_t GetNumSamplesInClip( std::string strClipName, bool bTail ) const;
	SDL_AudioSpec * GetAudioSpecPtr() const;
	Clip * GetClip( std::string strClipName ) const;

	// Add a clip to storage, can be recalled later as a Voice
	bool RegisterClip( std::string strClipName, std::string strHeadFile, std::string strTailFile, size_t uFadeDurationMS );

	// SDL Audio callback, will end up calling fill_audio_impl on a SoundManager instance
	static void FillAudio( void * pUserData, uint8_t * pStream, int nSamplesDesired );

	// The command pattern uses an enum to 
	// dictate what the command really means
	enum class ECommandID : int
	{
		//////////////////////////////////////////////////////////
		// These commands posted to the audio thread
		None = 0,		// NIL
		SetVolume,		// Set the volume of a voice
		StartVoice,		// Start a new voice and loop it
		StopVoice,		// Stop an active loop (and destroy it)
		StopVoices,		// Stop any playing voices (when they finish)
		OneShot,		// Start a new voice and play once
		//////////////////////////////////////////////////////////
		// These commands are posted by the audio thread
		BufCompleted,	// The audio thread has rendered a buffer 
		AllQuiet,		// There are no voices playing
	};

	// Command object, stores the necessary information
	// to carry out an action (and then some)
	struct Command
	{
		ECommandID eID{ ECommandID::None };	// What command is this
		Clip * pClip{ nullptr };			// What clip does it involve
		int iData{ -1 };					// Used for int data (i.e Voice ID)
		float fData{ 1.f };					// Used for float data (i.e volume)
		size_t uData{ 0 };					// Used for	size data (i.e sample pos)
	};

	// Handle one or more commands
	bool HandleCommand( Command cmd );
	bool HandleCommands( std::list<Command> cmd );

    // Set this to true to turn on sample pos printing
    void SetSamplePosPrinting(bool bPrint);

private:
	// Sort of a dumb typedef
	using AudioSpecPtr = std::unique_ptr<SDL_AudioSpec>;
	AudioSpecPtr m_pAudioSpec;				// Audio spec, describes loop format

	// Playback logic
	bool m_bPlaying;						// Whether or not we are filling buffers of audio
	size_t m_uMaxSampleCount;				// Sample count of longest clip in storage
	size_t m_uNumBufsCompleted;             // The number of buffers filled by the audio thread
	size_t m_uSamplePos;					// Current sample pos in playback, wraps around m_uMaxSampleCount

	// Inter-thread communication
	std::mutex m_muAudioMutex;				// Mutex controlling communication between audio and main threads
	std::list<Command> m_liPublicCmdQueue;	// Anyone can put tasks here, will be read by audio thread
	std::list<Command> m_liAudioCmdQueue;	// Audio thread's tasks, only modified by audio thread

	// Clip and voice storage
	std::map<std::string, Clip> m_mapClips;	// Clip storage, right now the map is a convenience
	std::list<Voice> m_liVoices;

	// The actual callback function used to fill audio buffers
	// (called from the static FillAudio function)
	void fill_audio_impl( uint8_t * pStream, int nBytesToFill );

	// Called by audio thread to get messages from main thread
	// and leave it with any data it might want
	void getMessagesFromMainThread( std::list<Command> liCommandsToPost );

	// Called by from ::Update to get messages from aud thread
	void getMessagesFromAudThread();

    // I'm using this mutex to control who prints to cout
    // so I can debug things between the audio/main threads
    std::mutex m_muPrintSamplePos;
    bool m_bPrintSamplePos;

public:
	static bool pylExpose();
};
