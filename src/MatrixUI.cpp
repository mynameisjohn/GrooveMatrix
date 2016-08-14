#include "MatrixUI.h"
#include "Util.h"

#include <glm/gtc/type_ptr.hpp>
#include <algorithm>


MatrixUI::MatrixUI() :
	m_bQuitFlag( false ),
	m_GLContext( nullptr ),
	m_pWindow( nullptr )
{
}

MatrixUI::~MatrixUI()
{
	if ( m_pWindow )
	{
		SDL_DestroyWindow( m_pWindow );
		m_pWindow = nullptr;
	}
	if ( m_GLContext )
	{
		SDL_GL_DeleteContext( m_GLContext );
		m_GLContext = nullptr;
	}
}

void MatrixUI::Draw()
{
	// Clear the screen
	glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT );

	// Bind the shader
	auto sBind = m_Shader.ScopeBind();

	// Get the camera mat as well as some handles
	GLuint pmvHandle = m_Shader.GetHandle( "u_PMV" );
	GLuint clrHandle = m_Shader.GetHandle( "u_Color" );
	mat4 P = m_Camera.GetCameraMat();

	// Draw every Drawable
	for ( Drawable& dr : m_vDrawables )
	{
		if ( dr.GetIsActive() == false )
			continue;

		mat4 PMV = P * dr.GetMV();
		vec4 c = dr.GetColor();
		glUniformMatrix4fv( pmvHandle, 1, GL_FALSE, glm::value_ptr( PMV ) );
		glUniform4fv( clrHandle, 1, glm::value_ptr( c ) );
		dr.Draw();
	}

	// Swap window
	SDL_GL_SwapWindow( m_pWindow );
}

void MatrixUI::Update()
{

}

// Add a drawable from an IQM file
int MatrixUI::AddDrawableIQM( std::string strIqmFile, vec2 T, vec2 S, vec4 C, float theta /*= 0.f*/ )
{
	Drawable D;
	try
	{
		// Assume rotation about z for now
		fquat qRot( cos( theta / 2 ), sin( theta / 2 ) * vec3( 0, 0, 1 ) );
		D.Init( strIqmFile, C, quatvec( vec3( T, 0 ), qRot, quatvec::Type::TR ), S );
	}
	catch ( std::runtime_error )
	{
		return -1;
	}

	m_vDrawables.push_back( D );
	return (int) (m_vDrawables.size() - 1);
}

// Add a drawable from three triangle verts
int MatrixUI::AddDrawableTri( std::string strName, std::array<vec3, 3> triVerts, vec2 T, vec2 S, vec4 C, float theta /*= 0.f*/ )
{
	Drawable D;
	try
	{
		// Assume rotation about z for now
		fquat qRot( cos( theta / 2 ), sin( theta / 2 ) * vec3( 0, 0, 1 ) );
		D.Init( strName, triVerts, C, quatvec( vec3( T, 0 ), qRot, quatvec::Type::TR ), S );
	}
	catch ( std::runtime_error )
	{
		return -1;
	}

	m_vDrawables.push_back( D );
	return (int) (m_vDrawables.size() - 1);
}

int MatrixUI::AddShape( Shape::EType eType, glm::vec2 v2Pos, std::map<std::string, float> mapDetails )
{
	using EType = Shape::EType;
	try
	{
		Shape sb;
		switch ( eType )
		{
			case EType::Circle:
			{
				float fRad = mapDetails.at( "r" );
				sb = Circle::Create( v2Pos, fRad );
				break;
			}
			case EType::AABB:
			{
				float w = mapDetails.at( "w" );
				float h = mapDetails.at( "h" );
				sb = AABB::Create( v2Pos, glm::vec2( w, h ) / 2.f );
				break;
			}
			case EType::Triangle:
			{
				vec2 a( mapDetails.at( "aX" ), mapDetails.at( "aY" ) );
				vec2 b( mapDetails.at( "bX" ), mapDetails.at( "bY" ) );
				vec2 c( mapDetails.at( "cX" ), mapDetails.at( "cY" ) );
				sb = Triangle::Create( v2Pos, a, b, c );
				break;
			}
			default:
				return -1;
		}

		m_vShapes.push_back( sb );
		return m_vShapes.size() - 1;
	}
	catch ( std::out_of_range )
	{
		std::cerr << "Error! Invalid details provided when creating Rigid Body!" << std::endl;
	}

	return -1;
}

const Shader * MatrixUI::GetShaderPtr() const
{
	return &m_Shader;
}

const Camera * MatrixUI::GetCameraPtr() const
{
	return &m_Camera;
}

const Drawable * MatrixUI::GetDrawable( const size_t drIdx ) const
{
	if ( drIdx < m_vDrawables.size() )
		return &m_vDrawables[drIdx];

	throw std::runtime_error( "Error: Drawable index out of bound!" );
	return nullptr;
}

const Shape * MatrixUI::GetShape( const size_t sbIdx ) const
{
	if ( sbIdx < m_vShapes.size() )
		return &m_vShapes[sbIdx];

	throw std::runtime_error( "Error: SB index out of bound!" );
	return nullptr;
}

void MatrixUI::SetQuitFlag( bool bQuit )
{
	m_bQuitFlag = bQuit;
}

bool MatrixUI::GetQuitFlag() const
{
	return m_bQuitFlag;
}

bool MatrixUI::InitDisplay( std::string strWindowName, vec4 v4ClearColor, std::map<std::string, int> mapDisplayAttrs )
{
	SDL_Window * pWindow = nullptr;
	SDL_GLContext glContext = nullptr;

	try
	{
		pWindow = SDL_CreateWindow( strWindowName.c_str(),
									mapDisplayAttrs["posX"],
									mapDisplayAttrs["posY"],
									mapDisplayAttrs["width"],
									mapDisplayAttrs["height"],
									mapDisplayAttrs["flags"] );

		SDL_GL_SetAttribute( SDL_GL_CONTEXT_MAJOR_VERSION, mapDisplayAttrs["glMajor"] );
		SDL_GL_SetAttribute( SDL_GL_CONTEXT_MINOR_VERSION, mapDisplayAttrs["glMinor"] );

		SDL_GL_SetAttribute( SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE );
		SDL_GL_SetAttribute( SDL_GL_DOUBLEBUFFER, mapDisplayAttrs["doubleBuf"] );

		glContext = SDL_GL_CreateContext( pWindow );
		if ( glContext == nullptr )
		{
			std::cout << "Error creating opengl context" << std::endl;
			return false;
		}

		//Initialize GLEW
		glewExperimental = GL_TRUE;
		GLenum glewError = glewInit();
		if ( glewError != GLEW_OK )
		{
			printf( "Error initializing GLEW! %s\n", glewGetErrorString( glewError ) );
			return false;
		}

		SDL_GL_SetSwapInterval( mapDisplayAttrs["vsync"] );

		glClearColor( v4ClearColor.x, v4ClearColor.y, v4ClearColor.z, v4ClearColor.w );

		glEnable( GL_DEPTH_TEST );
		glDepthMask( GL_TRUE );
		glDepthFunc( GL_LESS );
		glEnable( GL_MULTISAMPLE_ARB );

	}
	catch ( std::out_of_range e )
	{
		if ( pWindow )
			SDL_DestroyWindow( pWindow );

		if ( glContext )
			SDL_GL_DeleteContext( glContext );

		return false;
	}

	m_pWindow = pWindow;
	m_GLContext = glContext;

	return true;
}

bool MatrixUI::GetIsOverlapping( Shape * pA, Shape * pB ) const
{
	if ( pA && pB )
		return pA->IsOverlapping( pB );
}