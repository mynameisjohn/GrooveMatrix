#pragma once

#include <Python.h>
#include <glm/fwd.hpp>

namespace pyl
{
	bool convert( PyObject *, glm::vec2& );
	bool convert( PyObject *, glm::vec3& );
	bool convert( PyObject *, glm::vec4& );
	bool convert( PyObject *, glm::fquat& );
}