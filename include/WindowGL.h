#pragma once

// Owns a window, glctx, drawables+shapes, shader, camera
#include "Camera.h"
#include "Drawable.h"
#include "Shader.h"
#include "GL_Util.h"

#include <vector>

struct SDL_Window;
struct SDL_GLContext;

class WindowGL
{
	SDL_Window * m_pWindow;
	SDL_GLContext * m_pGLContext;
	Camera m_Camera;
	Shader m_Shader;
	std::vector<Drawable> m_vDrawables;

public:
	WindowGL();
	~WindowGL();

	bool Init( std::string strWindowName, vec4 v4ClearColor, std::map<std::string, int> mapDisplayAttrs );

};