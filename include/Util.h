#pragma once

#include <algorithm>

// Useful const pointer template
template<typename T>
using const_ptr = const T * const;

// remaps x : [m0, M0] to the range of [m1, M1]
template <typename T>
inline T remap( T x, T m0, T M0, T m1, T M1 )
{
	return m1 + ((x - m0) / (M0 - m0)) * (M1 - m1);
}

template<typename T>
T clamp( T x, T min, T max )
{
	return std::min( std::max( x, min ), max );
}

// Used for hashing pairs
template<typename P>
struct pair_hash
{
	template <class T>
	static inline void hash_combine( std::size_t & seed, const T& v )
	{
		std::hash<T> hasher;
		seed ^= hasher( v ) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
	}

	size_t operator()( const P& p ) const
	{
		std::size_t seed1 = 0;
		hash_combine( seed1, p.first );
		hash_combine( seed1, p.second );

		std::size_t seed2 = 0;
		hash_combine( seed2, p.second );
		hash_combine( seed2, p.first );

		size_t ret = std::min( seed1, seed2 );
		return ret;
	}
};

template <typename P>
struct pair_hash_eq
{
	bool operator()( const P& a, const P& b ) const
	{
		return pair_hash<P>()(a) == pair_hash<P>()(b);
	}
};
