#pragma once

#include <Python.h>
#include <glm/fwd.hpp>
#include "../include/ClipLauncher.h"
#include "/usr/local/include/SDL2/SDL.h"
#include "../include/Shape.h"

namespace pyl
{
	bool convert( PyObject *, glm::vec2& );
	bool convert( PyObject *, glm::vec3& );
	bool convert( PyObject *, glm::vec4& );
	bool convert( PyObject *, glm::fquat& );

    bool convert( PyObject * pObj, ClipLauncher::ECommandID& eID );
    PyObject * alloc_pyobject( const ClipLauncher::ECommandID& eID );
    bool convert( PyObject * pObj, ClipLauncher::Command& cmd );
    bool convert( PyObject * pObj, SDL_AudioSpec& spec );
    bool convert( PyObject * o, quatvec& qv );
    bool convert( PyObject * o, Shape::EType& e );
    PyObject * alloc_pyobject( const Shape::EType e );
    PyObject * alloc_pyobject( const glm::vec2& v ); 
}
