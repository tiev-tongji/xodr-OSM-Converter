/* Header file for robust predicates by Jonathan Richard Shewchuk */

#ifndef __PREDICATES_H__
#define __PREDICATES_H__

void exactinit(int verbose);

double orient2d (double * pa, double * pb, double * pc);
double incircle (double * pa, double * pb, double * pc, double * pd);

//double orient3d            (double * pa,
//                double * pb,
//                double * pc,
//                double * pd);

//double insphere            (double * pa,
//                double * pb,
//                double * pc,
//                double * pd,
//                double * pe);

#endif /* __PREDICATES_H__ */
