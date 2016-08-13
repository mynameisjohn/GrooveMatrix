#pragma once

#include "Util.h"

/***********************************************
Voice class - voices played by a SoundManager

Each voice owns a pointer to a clip object
containing a buffer of audio data. The voice
object renders that audio data to the SoundManager's
mix buffer in a "pull" method (RenderAudio).
Voices can render their clip data once (one shot)
or in a looping fashion with optional tail-out. 

The playback logic to manage how the a voice plays 
its clip is all contained within this class. 

A voice can be told to start or stop with some
trigger resolution indicating how many samples
must pass before the state change occcurs.
***********************************************/

// Forward clip here
class Clip;

// This has to be included
// because I can't forward
// a command, which is a scoped
// object of SoundManager. Is that
// worth it? I'd say no...
#include "ClipLauncher.h"

class Voice
{
	// Initializing constructor is private
	// Clients must construct with either
	// a sound manager command or a clip
	Voice();

public:
	// Construct with pointer to actual audio clip, trigger res, initial volume, and loop bool
	Voice( const_ptr<Clip>, int ID, size_t uTriggerRes, float fVolume, bool bLoop = false );

	// Construct with soundmanager command
	Voice( const ClipLauncher::Command cmd );

	// The playback logic for voices is controlled by a state
	// variable owned by Voice instances, enumerated as such
	enum class EState : int
	{
		Pending = 0,		// Start playing when the trigger res is hit
		OneShot,            // Play once when the trigger res is hit
		Starting,			// Play the head once and switch to looping on loop back
		Looping,			// Play the head and tail mixed until set to stopping
		Stopping,			// Acts like Starting or Looping, and on loop back plays tail only
		Tail,				// Play the tail only before transitioning to stopped
		TailPending,		// We've been set to start once the tail ends
		TailOneShot,        // Same as above, but switch to oneshot
		Stopped				// Renders no samples to buffer
	};

	// Possibly copy uSamplesDesired of float sampels into pMixBuffer
	void RenderData( float * const pMixBuffer, const size_t uSamplesDesired, const size_t uSamplePos );

	// Various gets
	EState GetState() const;
	EState GetPrevState() const;
	float GetVolume() const;
	int GetID() const;

	// Set the voice to start/stop at the trigger res
	void SetStopping( const size_t uTriggerRes );
	void SetPending( const size_t uTriggerRes, bool bLoop = false );

	// Set the volume
	void SetVolume( const float fVol );

private:
	int m_iUniqueID;                // The voice identifier, used to uniquely identify it
	EState m_eState;				// One of the above, determines where samples come from
	EState m_ePrevState;			// The previous state, used to control transitions
	float m_fVolume;                // Volume, each rendered sample is multiplied by this factor
	size_t m_uTriggerRes;           // When actions like starting and stopping occur
	size_t m_uStartingPos;          // Cached sample pos of when we last started playing
	size_t m_uLastTailSampleAdded;  // Cached pos of the last tail sample added
	Clip const * m_pClip;           // Pointer to the clip owning the buffer of audio

	// Internal function to set the state/prevState
	void setState ( EState eNextState );
};