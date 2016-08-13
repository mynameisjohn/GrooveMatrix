#include "GrooveMatrix.h"

GrooveMatrix::GrooveMatrix()
{

}

GrooveMatrix::~GrooveMatrix()
{

}

MatrixUI * GrooveMatrix::GetMatrixUI() const
{
	return (MatrixUI *)&m_MatrixUI;
}

ClipLauncher * GrooveMatrix::GetClipLauncher() const
{
	return (ClipLauncher *)&m_ClipLauncher;
}