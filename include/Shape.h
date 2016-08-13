#pragma once

#include "quatvec.h"
#include "Util.h"
#include "EntComponent.h"

#include <glm/mat2x2.hpp>
#include <glm/vec2.hpp>

#include <array>

struct Circle;
struct AABB;
struct Triangle;

// Why make this weird class?
// So I can keep all types of shapes
// inside the contiguous data structures
struct Shape : public EntComponent
{
	// Enum meant to represent the type of shape
	// (or rather, which union members mean something)
	enum class EType : int
	{
		None,
		Circle,
		AABB,
		Triangle
	};

	bool bActive;		// If the shape is in the mix
	EType eType;		// Primitive type
	glm::vec2 v2Center;	// Center position

	// The big union
	union
	{
		struct { float fRadius; };			// Circle Data
		struct { glm::vec2 v2HalfDim; };	// Box Data
		struct { glm::vec2 v2A, v2B, v2C; };// Triangle Data
	};

	Shape();
	Shape( glm::vec2 v2C );

	void SetIsActive( bool b );
	bool GetIsActive() const;

	glm::vec2 GetPosition() const;
	EType GetType() const;

	void SetCenterPos( glm::vec2 v2Pos );

	bool IsOverlapping( const_ptr<Shape> pOther ) const;
	bool IsPointInside( const glm::vec2 v2Point ) const;

	static bool pylExpose();

	static float cross2D( const glm::vec2& a, const glm::vec2& b );
	static glm::vec2 perp( const glm::vec2& v );
};

// General pattern here is
//		disabled default constructor
//		static factory methods that set prim type
struct Circle : public Shape
{
	Circle() = delete;

	static Shape Create( glm::vec2 c, float fRadius );

	float Radius() const;
};

struct AABB : public Shape
{
	AABB() = delete;

	// Static creation function, returns a RigidBody2D
	static Shape Create( glm::vec2 c, glm::vec2 v2R );
	static Shape Create( float x, float y, float w, float h );

	// useful things
	float Width() const;
	float Height() const;
	float Left() const;
	float Right() const;
	float Top() const;
	float Bottom() const;
	glm::vec2 Clamp( const glm::vec2 p ) const;
	glm::vec2 GetFaceNormalFromPoint( const glm::vec2 p ) const;
	glm::vec2 HalfDim() const;
	glm::vec2 GetVert( int idx ) const;
	glm::vec2 GetNormal( int idx ) const;
};

struct Triangle : public Shape
{
	Triangle() = delete;

	static Shape Create( glm::vec2 c, glm::vec2 A, glm::vec2 B, glm::vec2 C );

	float Left() const;
	float Right() const;
	float Top() const;
	float Bottom() const;
	std::array<glm::vec2, 3> Verts() const;
	std::array<glm::vec2, 3> Edges() const;
};