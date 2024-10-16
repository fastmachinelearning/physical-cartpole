#ifndef __NEURAL_IMITATOR_H_
#define __NEURAL_IMITATOR_H_

#define MLP_TOTAL_BITS_PER_VARIABLE	12
#define MLP_INTEGER_PLUS_SIGN_BITS_PER_VARIABLE	2

#define MLP_ACTIVATION_NEURONS		7 // 4bytes each
#define MLP_PREDICTION_NEURONS		1 // 4bytes each
#define DATA_WORD_BYTES				4

#define NETWORK_INPUT_SIZE_IN_BYTES		(MLP_ACTIVATION_NEURONS * DATA_WORD_BYTES)
#define NETWORK_OUTPUT_SIZE_IN_BYTES		(MLP_PREDICTION_NEURONS * DATA_WORD_BYTES)

void Neural_Imitator_Init();
void Neural_Imitator_Evaluate(unsigned char * network_input_buffer, unsigned char * network_output_buffer);
void Neural_Imitator_ReleaseResources();

float neural_imitator_cartpole_step(float angle, float angleD, float angle_cos, float angle_sin, float position, float positionD, float target_equilibrium, float target_position, float time);


#endif /*__NEURAL_IMITATOR_H_*/
