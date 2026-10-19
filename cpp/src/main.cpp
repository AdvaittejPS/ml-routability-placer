#include <iostream>
#include "../include/placer.h"
#include <string>

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "Usage: placer_cli <parsed_netlist.json> [out_csv]" << std::endl;
        return 1;
    }
    std::string path = argv[1];
    std::string out = "placement_out.csv";
    if (argc >= 3) out = argv[2];

    Design d;
    try {
        load_design_from_json(path, d);
    } catch (std::exception &e) {
        std::cerr << "Failed to load design: " << e.what() << std::endl;
        return 1;
    }

    initial_place_random(d);
    run_optimizer(d, 100, 4.0, 1.0, 1.0);
    write_placement_csv(d, out);
    std::cout << "Wrote placement to " << out << std::endl;
    return 0;
}
