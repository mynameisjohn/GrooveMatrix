#include "ClipLauncher.h"
#include "MatrixUI.h"

#include <SDL.h>
#include <pyliaison.h>

int main( int argc, char ** argv )
{
	try
	{
		EntComponent::pylExpose();
		Shader::pylExpose();
		Camera::pylExpose();
		Drawable::pylExpose();
		Shape::pylExpose();
		ClipLauncher::pylExpose();
		MatrixUI::pylExpose();
		pyl::initialize();

		MatrixUI M;
		ClipLauncher C;
		
		pyl::Object obMainScript = pyl::Object::from_script( "../scripts/main.py" );

		bool bInitSuccess = false;
		if ( obMainScript.call( "Initialize", &M, &C ).convert( bInitSuccess ) && bInitSuccess )
		{
			while ( M.GetQuitFlag() == false )
			{
				SDL_Event e;
				while ( SDL_PollEvent( &e ) )
				{
					obMainScript.call( "HandleEvent", &e );
				}
				obMainScript.call( "Update" );
			}
		}

		pyl::finalize();

	}
	catch ( pyl::runtime_error e )
	{
		std::cout << e.what() << std::endl;
		pyl::print_error();
		return -1;
	}

	
	return 0;
}