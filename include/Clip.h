#pragma once

#include <vector>
#include <string>

/***********************************************
Clip class - stores a buffer of audio

The clip class is really just a container/wrapper
for audio data that can be rendered by voices

Each voice owns a pointer to a clip from which
it draws its audio data. 
***********************************************/

class Clip
{
public:
	// Default constructor sets int members to zero
	Clip();

	// Data constructor does all the hard work
	Clip( const std::string strName,			// The friendly name of the clip
		  const float * const pHeadBuffer,		// The head buffer
		  const size_t uSamplesInHeadBuffer,	// and its sample count
		  const float * const pTailBuffer,		// The tail buffer
		  const size_t uSamplesInTailBuffer,	// and its sample count
		  const size_t m_uFadeSamples );		// The # of fade samples

	// Various gets
	std::string GetName() const;
	size_t GetNumSamples( bool bIncludeTail = false ) const;
	size_t GetNumFadeSamples() const;
	float const * GetAudioData() const;

private:
	size_t m_uSamplesInHead;					// The number of samples in the head
	size_t m_uFadeSamples;						// The fade duration for starting/stopping/looping, in samples
	std::string m_strName;						// The name of the loop (this is never touched by audio thread)
	std::vector<float> m_vAudioBuffer;			// The vector storing the entire head and tail (with fades baked?)
};