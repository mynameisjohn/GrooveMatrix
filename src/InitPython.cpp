#include "ClipLauncher.h"
#include "MatrixUI.h"
#include "Clip.h"

#include <pyliaison.h>

namespace pyl
{
	template<typename eType>
	bool convertEnum( PyObject * o, eType& e )
	{
		int tmp( 0 );
		if ( bool bRet = convert( o, tmp ) )
		{
			e = (eType) tmp;
			return bRet;
		}
		return false;
	}

	bool convert( PyObject * pObj, ClipLauncher::ECommandID& eID )
	{
		return convertEnum<ClipLauncher::ECommandID>( pObj, eID );
	}
	PyObject * alloc_pyobject( const ClipLauncher::ECommandID& eID )
	{
		return PyLong_FromLong( (long) eID );
	}
	bool convert( PyObject * pObj, ClipLauncher::Command& cmd )
	{
		std::tuple<ClipLauncher::ECommandID, Clip *, int, float, size_t> tup;
		if ( convert( pObj, tup ) )
		{
			cmd.eID = std::get<0>( tup );
			cmd.pClip = std::get<1>( tup );
			cmd.iData = std::get<2>( tup );
			cmd.fData = std::get<3>( tup );
			cmd.uData = std::get<4>( tup );
			return true;
		}
		return false;
	}
	bool convert( PyObject * pObj, SDL_AudioSpec& spec )
	{
		SDL_AudioSpec * pSpec = nullptr;
		if ( pObj && convert( pObj, pSpec ) && pSpec )
		{
			spec = *pSpec;
			return true;
		}
		return false;
	}

	bool convert( PyObject * o, glm::vec2& v )
	{
		return convert_buf( o, &v[0], sizeof( v ) / sizeof( float ) );
	}
	bool convert( PyObject * o, glm::vec3& v )
	{
		return convert_buf( o, &v[0], sizeof( v ) / sizeof( float ) );
	}
	bool convert( PyObject * o, glm::vec4& v )
	{
		return convert_buf( o, &v[0], sizeof( v ) / sizeof( float ) );
	}
	bool convert( PyObject * o, glm::fquat& v )
	{
		return convert_buf( o, &v[0], sizeof( v ) / sizeof( float ) );
	}

	// Type? Should be part of this...
	bool convert( PyObject * o, quatvec& qv )
	{
		return convert_buf( o, &qv.vec[0], 7 );
	}

	bool convert( PyObject * o, Shape::EType& e )
	{
		return convertEnum<Shape::EType>( o, e );
	}

	PyObject * alloc_pyobject( const Shape::EType e )
	{
		return PyLong_FromLong( (long) e );
	}

	template <typename glmType>
	PyObject * alloc_glm_type( const glmType& v )
	{
		return alloc_buf<float>(&v[0], sizeof( v ) / sizeof( float ));
	}

	PyObject * alloc_pyobject( const glm::vec2& v )
	{
		return alloc_glm_type( v );
	}
	PyObject * alloc_pyobject( const glm::vec3& v )
	{
		return alloc_glm_type( v );
	}
	PyObject * alloc_pyobject( const glm::vec4& v )
	{
		return alloc_glm_type( v );
	}
	PyObject * alloc_pyobject( const glm::fquat& q )
	{
		return alloc_glm_type( q );
	}
}

#define CREATE_AND_TEST_MOD(modName)\
		pyl::ModuleDef * pModDef = CreateMod( modName );\
		if ( pModDef == nullptr ){\
			throw pyl::runtime_error("Error creating module ##modName");\
		}

/*static*/ bool EntComponent::pylExpose()
{
	CREATE_AND_TEST_MOD( EntComponent );
	AddClassToMod( pModDef, EntComponent );
	AddMemFnToMod( pModDef, EntComponent, SetEntID, void, int );
	AddMemFnToMod( pModDef, EntComponent, GetEntID, int );
	return true;
}

/*static*/ bool Shape::pylExpose()
{
	CREATE_AND_TEST_MOD( Shape );

	pyl::ModuleDef * pEntMod = pyl::ModuleDef::GetModuleDef( "EntComponent" );
	AddSubClassToMod( pModDef, Shape, pEntMod, EntComponent );

	AddMemFnToMod( pModDef, Shape, GetPosition, vec2 );
	AddMemFnToMod( pModDef, Shape, GetType, EType );
	AddMemFnToMod( pModDef, Shape, SetCenterPos, void, vec2 );
	AddMemFnToMod( pModDef, Shape, GetIsActive, bool );
	AddMemFnToMod( pModDef, Shape, SetIsActive, void, bool );

	pModDef->SetCustomModuleInit( [] ( pyl::Object obModule )
	{
		obModule.set_attr( "Circle", EType::Circle );
		obModule.set_attr( "AABB", EType::AABB );
		obModule.set_attr( "Triangle", EType::Triangle );
	} );

	return true;
}

/*static*/ bool ClipLauncher::pylExpose()
{
	CREATE_AND_TEST_MOD( ClipLauncher );

	AddClassToMod( pModDef, ClipLauncher );

	AddMemFnToMod( pModDef, ClipLauncher, Init, bool, SDL_AudioSpec * );
	AddMemFnToMod( pModDef, ClipLauncher, Update, void );
	AddMemFnToMod( pModDef, ClipLauncher, GetPlayPause, bool );
	AddMemFnToMod( pModDef, ClipLauncher, SetPlayPause, void, bool );
	AddMemFnToMod( pModDef, ClipLauncher, GetMaxSampleCount, size_t );
	AddMemFnToMod( pModDef, ClipLauncher, GetSampleRate, size_t );
	AddMemFnToMod( pModDef, ClipLauncher, GetBufferSize, size_t );
	AddMemFnToMod( pModDef, ClipLauncher, GetNumBufsCompleted, size_t );
	AddMemFnToMod( pModDef, ClipLauncher, GetNumSamplesInClip, size_t, std::string, bool );
	AddMemFnToMod( pModDef, ClipLauncher, GetAudioSpecPtr, SDL_AudioSpec * );
	AddMemFnToMod( pModDef, ClipLauncher, RegisterClip, bool, std::string, std::string, std::string, size_t );
	AddMemFnToMod( pModDef, ClipLauncher, GetClip, Clip *, std::string );
	AddMemFnToMod( pModDef, ClipLauncher, HandleCommand, bool, Command );
	AddMemFnToMod( pModDef, ClipLauncher, HandleCommands, bool, std::list<Command> );

	pModDef->SetCustomModuleInit( [] ( pyl::Object obModule )
	{
		obModule.set_attr( "cmdNone", ClipLauncher::ECommandID::None );
		obModule.set_attr( "cmdSetVolume", ClipLauncher::ECommandID::SetVolume );
		obModule.set_attr( "cmdStartVoice", ClipLauncher::ECommandID::StartVoice );
		obModule.set_attr( "cmdStopVoice", ClipLauncher::ECommandID::StopVoice );
		obModule.set_attr( "cmdStopVoices", ClipLauncher::ECommandID::StopVoices );
		obModule.set_attr( "cmdOneShot", ClipLauncher::ECommandID::OneShot );
	} );

	// Also add the clip class
	AddClassToMod( pModDef, Clip );
	AddMemFnToMod( pModDef, Clip, GetName, std::string );
	AddMemFnToMod( pModDef, Clip, GetNumSamples, size_t, bool );
	AddMemFnToMod( pModDef, Clip, GetNumFadeSamples, size_t );

	return true;
}

/*static*/ bool MatrixUI::pylExpose()
{
	CREATE_AND_TEST_MOD( MatrixUI );

	AddClassToMod( pModDef, MatrixUI );

	AddMemFnToMod( pModDef, MatrixUI, InitDisplay, bool, std::string, vec4, std::map<std::string, int> );
	AddMemFnToMod( pModDef, MatrixUI, GetShaderPtr, const Shader * );
	AddMemFnToMod( pModDef, MatrixUI, GetCameraPtr, const Camera * );
	AddMemFnToMod( pModDef, MatrixUI, GetDrawable, const Drawable *, const size_t );
	AddMemFnToMod( pModDef, MatrixUI, GetShape, const Shape *, const size_t );
	AddMemFnToMod( pModDef, MatrixUI, AddDrawableTri, int, std::string, std::array<vec3, 3>, vec2, vec2, vec4, float );
	AddMemFnToMod( pModDef, MatrixUI, AddDrawableIQM, int, std::string, vec2, vec2, vec4, float );
	AddMemFnToMod( pModDef, MatrixUI, AddShape, int, Shape::EType, glm::vec2, std::map<std::string, float> );
	AddMemFnToMod( pModDef, MatrixUI, GetQuitFlag, bool );
	AddMemFnToMod( pModDef, MatrixUI, SetQuitFlag, void, bool );
	AddMemFnToMod( pModDef, MatrixUI, GetIsOverlapping, bool, Shape *, Shape * );
	AddMemFnToMod( pModDef, MatrixUI, Update, void );
	AddMemFnToMod( pModDef, MatrixUI, Draw, void );

	return true;
}

/*static*/ bool Shader::pylExpose()
{
	CREATE_AND_TEST_MOD( Shader );

	AddClassToMod( pModDef, Shader );
	AddMemFnToMod( pModDef, Shader, Init, bool, std::string, std::string, bool );
	AddMemFnToMod( pModDef, Shader, PrintLog_V, int );
	AddMemFnToMod( pModDef, Shader, PrintLog_F, int );
	AddMemFnToMod( pModDef, Shader, PrintSrc_V, int );
	AddMemFnToMod( pModDef, Shader, PrintSrc_F, int );
	AddMemFnToMod( pModDef, Shader, PrintLog_P, int );
	AddMemFnToMod( pModDef, Shader, GetHandle, GLint, const std::string );

	return true;
}

/*static*/ bool Camera::pylExpose()
{
	CREATE_AND_TEST_MOD( Camera );

	AddClassToMod( pModDef, Camera );
	AddMemFnToMod( pModDef, Camera, InitOrtho, void, int, int, float, float, float, float );
	AddMemFnToMod( pModDef, Camera, InitPersp, void, int, int, float, float, float, float );
	AddMemFnToMod( pModDef, Camera, GetAspectRatio, float );
	AddMemFnToMod( pModDef, Camera, GetScreenWidth, int );
	AddMemFnToMod( pModDef, Camera, GetScreenHeight, int );

	// The macro doesn't work out for static functions...
	auto SetCamMatHandle = Camera::SetCamMatHandle;
	AddFnToMod( pModDef, SetCamMatHandle );

	return true;
}

/*static*/ bool Drawable::pylExpose()
{
	CREATE_AND_TEST_MOD( Drawable );

	pyl::ModuleDef * pEntMod = pyl::ModuleDef::GetModuleDef( "EntComponent" );
	AddSubClassToMod( pModDef, Drawable, pEntMod, EntComponent );

	AddMemFnToMod( pModDef, Drawable, SetPos2D, void, vec2 );
	AddMemFnToMod( pModDef, Drawable, GetPos, vec3 );
	AddMemFnToMod( pModDef, Drawable, SetTransform, void, quatvec );
	AddMemFnToMod( pModDef, Drawable, SetColor, void, glm::vec4 );
	AddMemFnToMod( pModDef, Drawable, GetIsActive, bool );
	AddMemFnToMod( pModDef, Drawable, SetIsActive, void, bool );

	// The macro doesn't work out for static functions...
	auto SetPosHandle = Drawable::SetPosHandle;
	AddFnToMod( pModDef, SetPosHandle );

	auto SetColorHandle = Drawable::SetColorHandle;
	AddFnToMod( pModDef, SetColorHandle );

	return true;
}
