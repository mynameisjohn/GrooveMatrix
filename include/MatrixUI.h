#pragma once

#include "Camera.h"
#include "Shader.h"
#include "Drawable.h"
#include "Shape.h"
#include "Util.h"

#include <SDL.h>

#include <vector>
#include <array>
#include <unordered_map>

class MatrixUI
{
public:

	using ColPair = std::pair<Shape *, Shape *>;
	using ColBank = std::unordered_map < ColPair, bool, pair_hash<ColPair>, pair_hash_eq<ColPair>>;

	MatrixUI();
	~MatrixUI();

	bool InitDisplay( std::string strWindowName, vec4 v4ClearColor, std::map<std::string, int> mapDisplayAttrs );
	
	void Draw();
	void Update();

	void SetQuitFlag( bool bQuit );
	bool GetQuitFlag() const;

	bool GetIsOverlapping( Shape * pA, Shape * pB ) const;

	const Shader * GetShaderPtr() const;
	const Camera * GetCameraPtr() const;
	const Drawable * GetDrawable( const size_t drIdx ) const;
	const Shape * GetShape( const size_t sIdx ) const;	
	
	int AddDrawableIQM( std::string strIqmFile, vec2 T, vec2 S, vec4 C, float theta = 0.f );
	int AddDrawableTri( std::string strName, std::array<vec3, 3> triVerts, vec2 T, vec2 S, vec4 C, float theta = 0.f );
	int AddShape( Shape::EType eType, glm::vec2 v2Pos, std::map<std::string, float> mapDetails );

	static bool pylExpose();

private:
	bool m_bQuitFlag;
	SDL_GLContext m_GLContext;
	SDL_Window * m_pWindow;
	Shader m_Shader;
	Camera m_Camera;
	std::vector<Drawable> m_vDrawables;
	std::vector<Shape> m_vShapes;
	ColBank m_CollisionBank;
};
