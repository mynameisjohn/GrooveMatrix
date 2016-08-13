#include "GrooveMatrix.h"

#include <SDL.h>
#include <pyliaison.h>

int main( int argc, char ** argv )
{
	try
	{
		Shader::pylExpose();
		Camera::pylExpose();
		Drawable::pylExpose();
		Shape::pylExpose();
		ClipLauncher::pylExpose();
		MatrixUI::pylExpose();
		GrooveMatrix::pylExpose();
		pyl::initialize();

		pyl::finalize();
	}
	catch ( ...)
	{
		pyl::print_error();
		return -1;
	}

	return 0;
}