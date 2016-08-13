#pragma once

class EntComponent
{
	int m_iUniqueID;
public:
	EntComponent() :
		m_iUniqueID( -1 )
	{
	}
	inline void SetEntID( const int id )
	{
		m_iUniqueID = id;
	}
	inline int GetEntID() const
	{
		return m_iUniqueID;
	}

	static bool pylExpose();
};