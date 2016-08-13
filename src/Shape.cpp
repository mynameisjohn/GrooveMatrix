#include "Shape.h"
#include "GL_Util.h"

#include <glm/glm.hpp>
#include <glm/gtx/norm.hpp>

#include <algorithm>

Shape::Shape() :
	bActive( false ),
	eType( EType::None )
{
}

Shape::Shape( glm::vec2 v2C ) :
	bActive( false ),
	eType( EType::None ),
	v2Center( v2C )
{
}

void Shape::SetCenterPos( glm::vec2 v2Pos )
{
	v2Center = v2Pos;
}

vec2 Shape::GetPosition() const
{
	return v2Center;
}

Shape::EType Shape::GetType() const
{
	return eType;
}

void Shape::SetIsActive( bool b )
{
	bActive = b;
}

bool Shape::GetIsActive() const
{
	return bActive;
}

/*static*/ vec2 Shape::perp( const vec2& v )
{
	return vec2( -v.y, v.x );
}

/*static*/ float Shape::cross2D( const vec2& a, const vec2& b )
{
	return a.x*b.y - a.y*b.x;
}

bool TestOverlap( const_ptr<Circle>, const_ptr<Circle> );
bool TestOverlap( const_ptr<Circle>, const_ptr<AABB> );
bool TestOverlap( const_ptr<Circle>, const_ptr<Triangle> );
bool TestOverlap( const_ptr<AABB>, const_ptr<AABB> );
bool TestOverlap( const_ptr<AABB>, const_ptr<Triangle> );
bool TestOverlap( const_ptr<Triangle>, const_ptr<Triangle> ) { return false; }
bool TestPoint( const_ptr<Circle>, const vec2 v2Point );
bool TestPoint( const_ptr<AABB>, const vec2 v2Point );
bool TestPoint( const_ptr<Triangle>, const vec2 v2Point ) { return false; }
vec2 ClosestPtToTriangle( vec2 vA, vec2 vB, vec2 vC, vec2 p );

bool Shape::IsOverlapping( const_ptr<Shape> pOther ) const
{
	switch ( eType )
	{
		case EType::Circle:
		{
			switch ( pOther->eType )
			{
				case EType::Circle:
					return TestOverlap( (const_ptr<Circle>)this, (const_ptr<Circle>)pOther );
				case EType::AABB:
					return TestOverlap( (const_ptr<Circle>)this, (const_ptr<AABB>)pOther );
				case EType::Triangle:
					return TestOverlap( (const_ptr<Circle>)this, (const_ptr<Triangle>)pOther );
				default:
					break;
			}
			break;
		}
		case EType::AABB:
		{
			switch ( pOther->eType )
			{
				case EType::Circle:
					return TestOverlap( (const_ptr<Circle>)pOther, (const_ptr<AABB>)this );
				case EType::AABB:
					return TestOverlap( (const_ptr<AABB>)this, (const_ptr<AABB>)pOther );
				case EType::Triangle:
					return TestOverlap( (const_ptr<AABB>)this, (const_ptr<Triangle>)pOther );
				default:
					break;
			}
			break;
		}
		case EType::Triangle:
		{
			switch ( pOther->eType )
			{
				case EType::Circle:
					return TestOverlap( (const_ptr<Circle>)pOther, (const_ptr<Triangle>)this );
				case EType::AABB:
					return TestOverlap( (const_ptr<AABB>)pOther, (const_ptr<Triangle>)this );
				case EType::Triangle:
					return TestOverlap( (const_ptr<Triangle>)this, (const_ptr<Triangle>)pOther );
				default:
					break;
			}
			break;
		}
	}

	throw std::runtime_error( "Error: Invalid rigid body type!" );
	return false;
}

////////////////////////////////////////////////////////////////////////////

bool Shape::IsPointInside( const glm::vec2 v2Point ) const
{
	switch ( eType )
	{
		case EType::Circle:
			return TestPoint( const_ptr<Circle>( this ), v2Point );
		case EType::AABB:
			return TestPoint( const_ptr<AABB>( this ), v2Point );
		case EType::Triangle:
			return TestPoint( const_ptr<Triangle>( this ), v2Point );
	}

	throw std::runtime_error( "Error: Invalid rigid body type!" );
	return false;
}

////////////////////////////////////////////////////////////////////////////

/*static*/ Shape Circle::Create( glm::vec2 c, float fRadius )
{
	Shape ret( c );
	ret.fRadius = fRadius;
	ret.eType = Shape::EType::Circle;
	ret.bActive = true;
	return ret;
}

////////////////////////////////////////////////////////////////////////////

float Circle::Radius() const
{
	return fRadius;
}

////////////////////////////////////////////////////////////////////////////

bool TestOverlap( const_ptr<Circle> pA, const_ptr<Circle> pB )
{
	float fDist2 = glm::distance2( pA->v2Center, pB->v2Center );
	float fTotalRadius = pA->Radius() + pB->Radius();
	return fDist2 <= powf( fTotalRadius, 2 );
}

////////////////////////////////////////////////////////////////////////////

bool TestOverlap( const_ptr<Circle> pCirc, const_ptr<AABB> pAABB )
{
	vec2 ptClosest = pAABB->Clamp( pCirc->v2Center );
	return glm::distance2( ptClosest, pCirc->v2Center ) <= powf( pCirc->Radius(), 2 );
}

////////////////////////////////////////////////////////////////////////////

bool TestOverlap( const_ptr<Circle> pCirc, const_ptr<Triangle> pTri )
{
	vec2 p = ClosestPtToTriangle( pTri->v2A + pTri->v2Center, pTri->v2B + pTri->v2Center, pTri->v2C + pTri->v2Center, pCirc->v2Center );
	float f1 = glm::distance2( pCirc->v2Center, p );
	return f1 <= powf( pCirc->fRadius, 2 );
}

////////////////////////////////////////////////////////////////////////////

bool IsPointInside( vec2 p, Circle * pCirc )
{
	return glm::length2( pCirc->v2Center - p ) < powf( pCirc->fRadius, 2 );
}

////////////////////////////////////////////////////////////////////////////

float Triangle::Left() const
{
	return std::min( { v2A.x, v2B.x, v2C.x } ) + v2Center.x;
}

float Triangle::Right() const
{
	return std::max( { v2A.x, v2B.x, v2C.x } ) + v2Center.x;
}

float Triangle::Bottom() const
{
	return std::min( { v2A.y, v2B.y, v2C.y } ) + v2Center.y;
}

float Triangle::Top() const
{
	return std::max( { v2A.y, v2B.y, v2C.y } ) + v2Center.y;
}

std::array<glm::vec2, 3> Triangle::Verts() const
{
	return{ v2A + v2Center, v2B + v2Center, v2C + v2Center };
}

std::array<glm::vec2, 3> Triangle::Edges() const
{
	return{ v2B - v2A, v2C - v2B, v2A - v2C, };
}

////////////////////////////////////////////////////////////////////////////

float AABB::Width() const
{
	return 2.f * v2HalfDim.x;
}

float AABB::Height() const
{
	return 2.f * v2HalfDim.y;
}

float AABB::Left() const
{
	return v2Center.x - v2HalfDim.x;
}

float AABB::Right() const
{
	return v2Center.x + v2HalfDim.x;
}

float AABB::Top() const
{
	return v2Center.y + v2HalfDim.y;
}

float AABB::Bottom() const
{
	return v2Center.y - v2HalfDim.y;
}

glm::vec2 AABB::HalfDim() const
{
	return v2HalfDim;
}

glm::vec2 AABB::Clamp( const glm::vec2 p ) const
{
	return glm::clamp( p, v2Center - v2HalfDim, v2Center + v2HalfDim );
}

////////////////////////////////////////////////////////////////////////////

glm::vec2 AABB::GetFaceNormalFromPoint( const glm::vec2 p ) const
{
	vec2 n( 0 );

	if ( p.x < Right() && p.x > Left() )
	{
		if ( p.y < Bottom() )
			n = vec2( 0, -1 );
		else
			n = vec2( 0, 1 );
	}
	else
	{
		if ( p.x < Left() )
			n = vec2( -1, 0 );
		else
			n = vec2( 1, 0 );
	}

	return n;
}

////////////////////////////////////////////////////////////////////////////

/*static*/ Shape AABB::Create( glm::vec2 c, glm::vec2 v2R )
{
	Shape ret( c );
	ret.v2HalfDim = v2R;
	ret.eType = EType::AABB;
	ret.bActive = true;
	return ret;
}

////////////////////////////////////////////////////////////////////////////

/*static*/ Shape AABB::Create( float x, float y, float w, float h )
{
	Shape ret( vec2( x, y ) );
	ret.v2HalfDim = vec2( w, h ) / 2.f;
	ret.eType = EType::AABB;
	ret.bActive = true;
	return ret;
}

////////////////////////////////////////////////////////////////////////////

bool TestPoint( const_ptr<Circle> pCirc, const vec2 v2Point )
{
	return glm::length2( pCirc->v2Center - v2Point ) < powf( pCirc->fRadius, 2 );
}

////////////////////////////////////////////////////////////////////////////

bool TestPoint( const_ptr<AABB> pAABB, const vec2 v2Point )
{
	bool bX = fabs( v2Point.x - pAABB->v2Center.x ) < pAABB->v2HalfDim.x;
	bool bY = fabs( v2Point.y - pAABB->v2Center.y ) < pAABB->v2HalfDim.y;
	return bX && bY;
}

////////////////////////////////////////////////////////////////////////////

bool IsOverlappingX( const_ptr<AABB> pA, const_ptr<AABB> pB )
{
	return (pA->Right() < pB->Left() || pA->Left() > pB->Right()) == false;
}

bool IsOverlappingY( const_ptr<AABB> pA, const_ptr<AABB> pB )
{
	return (pA->Top() < pB->Bottom() || pA->Bottom() > pB->Top()) == false;
}

bool TestOverlap( const_ptr<AABB> pA, const_ptr<AABB> pB )
{
	return IsOverlappingX( pA, pB ) && IsOverlappingY( pA, pB );
}

////////////////////////////////////////////////////////////////////////////

bool TestOverlap( const_ptr<AABB> pAABB, const_ptr<Triangle> pTri )
{
	// Test box axes - treat triangle as a box, return false if separating axis
	if ( pTri->Right() < pAABB->Left() )
		return false;
	if ( pTri->Left() > pAABB->Right() )
		return false;
	if ( pTri->Top() < pAABB->Bottom() )
		return false;
	if ( pTri->Bottom() > pAABB->Top() )
		return false;

	// If that didn't work, make box center the origin
	std::array<vec2, 3> av2Verts = pTri->Verts();
	for ( vec2& v : av2Verts )
		v -= pAABB->v2Center;

	// Walk the face edges
	for ( const vec2& e : pTri->Edges() )
	{
		// See if the face normal is a separating axis
		vec2 n = Shape::perp( e );

		// The box extents along the normal
		float r = glm::dot( glm::abs( n ), pAABB->v2HalfDim );

		// The triangle extents along the normal
		float pA = glm::dot( av2Verts[0], n );
		float pB = glm::dot( av2Verts[1], n );
		float pC = glm::dot( av2Verts[2], n );

		// If n is a separating axis, get out
		if ( std::max( { pA, pB, pC } ) < -r )
			return false;
		if ( std::min( { pA, pB, pC } ) > r )
			return false;
	}

	// No separating axis found, return true
	return true;
}

////////////////////////////////////////////////////////////////////////////

glm::vec2 AABB::GetVert( int idx ) const
{
	vec2 ret( 0 );						// 3---0
	switch ( (idx + 4) % 4 )			// |   |
	{									// 2---1
		case 0:
			return v2Center + v2HalfDim;
		case 1:
			return v2Center + vec2( v2HalfDim.x, -v2HalfDim.y );
		case 2:
			return v2Center - v2HalfDim;
		case 3:
		default:
			return v2Center + vec2( -v2HalfDim.x, v2HalfDim.y );
	}
}

////////////////////////////////////////////////////////////////////////////

glm::vec2 AABB::GetNormal( int idx ) const
{										// --0--
	switch ( (idx + 4) % 4 )			// 3   1
	{									// --2--
		case 0:
			return vec2( 1, 0 );
		case 1:
			return vec2( 0, -1 );
		case 2:
			return vec2( -1, 0 );
		case 3:
		default:
			return vec2( 0, 1 );
	}
}

vec2 ClosestPtToTriangle( vec2 vA, vec2 vB, vec2 vC, vec2 p )
{
	// Face edges
	vec2 ab = vB - vA, ac = vC - vA, bc = vC - vB;

	float s_ab = glm::dot( p - vA, ab );		// unnormalized along ab
	float s_ba = glm::dot( p - vB, -ab );	// unnormalized along ba

	float t_bc = glm::dot( p - vB, bc );		// unnormalized along bc
	float t_cb = glm::dot( p - vC, -bc );	// and along cb

	float u_ac = glm::dot( p - vA, ac );		// along ac
	float u_ca = glm::dot( p - vC, -ac );	// along ca

											// If the unnormalized param from a to b
											// and from a to c is negative, a is closest
	if ( s_ab <= 0 && u_ac <= 0 )
		return vA;

	// If the unnormalized param from b to a
	// and from b to c is negative, b is closest
	if ( s_ba <= 0 && t_bc <= 0 )
		return vB;

	// If the unnormalized param from c to a
	// and from c to b is negative, c is closest
	if ( u_ca <= 0 && t_cb <= 0 )
		return vC;

	// If it wasn't one of those, check the edges
	// For each face edge, create a new triangle
	// with p as one of the verts and find its
	// signed area (positive half determined by n)
	float n = Shape::cross2D( ab, ac );

	// If proj(p, AB) is between A and B (both params positive)
	// check the signed area of pab, return proj if negative
	if ( s_ab > 0 && s_ba > 0 )
	{
		float sA_ab = n * Shape::cross2D( vA - p, vB - p );
		if ( sA_ab <= 0 )
		{
			float s = s_ab / (s_ab + s_ba);
			return vA + s * ab;
		}
	}

	// BC
	if ( t_bc > 0 && t_cb > 0 )
	{
		float sA_bc = n * Shape::cross2D( vB - p, vC - p );
		if ( sA_bc <= 0 )
		{
			float t = t_bc / (t_bc + t_cb);
			return vB + t * bc;
		}
	}

	// CA (note that ac goes from a to c, so we go from v2A)
	if ( u_ac > 0 && u_ca > 0 )
	{
		float sA_ca = n * Shape::cross2D( vC - p, vA - p );
		if ( sA_ca <= 0 )
		{
			float u = u_ac / (u_ac + u_ca);
			return vA + u * ac;
		}
	}

	// Inside triangle, return p
	return p;
}

Shape Triangle::Create( glm::vec2 c, glm::vec2 A, glm::vec2 B, glm::vec2 C )
{
	Shape ret( c );
	ret.eType = EType::Triangle;
	ret.v2A = A;
	ret.v2B = B;
	ret.v2C = C;
	ret.bActive = true;
	return ret;
}