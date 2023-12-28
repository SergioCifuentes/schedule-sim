# Schedule Simulator

Algorithm that provides solutions to class schedules based on teacher availability, size and classroom availability, fed from database scripts. Use of heuristic algorithms.

## Installation

To run the classroom programming simulation using Docker and a Conda image, follow these step-by-step installation instructions:

### Install Docker
If you do not already have Docker installed on your system, you can download and install it by following the official installation guide for your operating system:
[Windows](https://docs.docker.com/desktop/install/windows-install/)
[Linux](https://docs.docker.com/desktop/install/linux-install/)
[MacOS](https://docs.docker.com/desktop/install/mac-install/)

### Clone Repository
Clone the mock repository from the source code repository (e.g. GitHub) to your local machine:
```
git clone https://github.com/SergioCifuentes/schedule-sim
```

### Create Docker Image
Navigate to the root directory of the cloned repository and build the Docker image using the Dockerfile provided. Replace your image name with the name of the image you want:
```
cd your-simulation docker build -t your-image-name .
```

### Run Docker container
Now that you have created the Docker image, you can run a Docker container from it. Replace `your-image-name` with a meaningful name for your container:
```
docker run -it --name your-container-name your-image-name
```
And finally you will be able to access the application through localhost:5000.

## Configuration

Uploading CSV files is essential to the functionality of the simulation. Here you will see
all the files necessary to achieve a correct simulation.
To begin, all the files need to be in a single directory, thisso that when loading the files you only have to pass the PATH of the directory and these are the files it should contain.

![image](https://github.com/SergioCifuentes/schedule-sim/assets/47203526/f64e0fa0-c78e-4006-acf4-047a7ef41cf6)

You can change configurations in **constant.py**, like minutes in a period and the solver to use.

## Linear Programming Properties

Every rule for the linear programming algorithm can be found here **scheduler.py**

### Decision Variables
**X_it**: Binary decision variable that is equal to 1 if class i is scheduled at time t; 0
otherwise.
**Y_itj**: Binary decision variable that is equal to 1 if class i is scheduled at time t
assigned to teacher j; 0 otherwise.
**Z_itf**: Binary decision variable that is equal to 1 if class i is scheduled at time t
assigned to room f; 0 otherwise.

### Objective function:
The objective of the linear programming model is to maximize the assignment of courses and
Minimize scheduling conflicts. We can declare the objective function as a variable that will be established by the user according to what they want to search for when performing the simulation The objective function is as follows:
```
Maximize: Σ(X_it ) for all i, t
```

## Documentation

Documentation can be found in the `docs` directory.

## Contact Information
Sergio Cifuentes
Email: sergiocifuentes1485@gmail.com
