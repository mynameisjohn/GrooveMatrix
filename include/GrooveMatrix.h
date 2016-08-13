#pragma once

#include "MatrixUI.h"
#include "ClipLauncher.h"

class GrooveMatrix
{
public:
	GrooveMatrix();
	~GrooveMatrix();	

	MatrixUI * GetMatrixUI() const;
	ClipLauncher * GetClipLauncher() const;

	static bool pylExpose();

private:
	MatrixUI m_MatrixUI;
	ClipLauncher m_ClipLauncher;
};
