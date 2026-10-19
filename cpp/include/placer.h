#pragma once

#include <string>
#include <vector>

struct Instance {
    std::string name;
    std::string type;
    double width;
    double height;
    double x;
    double y;
};

struct PinRef {
    std::string instance;
    std::string pin;
};

struct Net {
    std::string name;
    std::vector<PinRef> pins;
};

struct Design {
    double width;
    double height;
    std::vector<Instance> instances;
    std::vector<Net> nets;
};

void load_design_from_json(const std::string &path, Design &d);
void initial_place_random(Design &d);
double compute_smoothed_hpwl(const Design &d, double alpha, std::vector<std::pair<double,double>> &grad);
void run_optimizer(Design &d, int iterations, double alpha, double lambda_density, double gamma_ml);
void write_placement_csv(const Design &d, const std::string &out_path);
