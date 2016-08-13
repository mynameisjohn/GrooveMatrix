#version 120

uniform mat4 u_PMV;

attribute vec3 a_Pos;

void main(){
	gl_Position = u_PMV * vec4(a_Pos, 1.0);	
}