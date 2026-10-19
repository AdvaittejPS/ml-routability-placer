#include "../include/placer.h"
#include <fstream>
#include <iostream>
#include <random>
#include <nlohmann/json.hpp>
#include <cmath>

using json = nlohmann::json;

void load_design_from_json(const std::string &path, Design &d) {
    std::ifstream ifs(path);
    if (!ifs) throw std::runtime_error("Failed to open json");
    json j; ifs >> j;
    d.width = 1000; d.height = 1000;
    d.instances.clear(); d.nets.clear();
    for (auto &it : j["instances"]) {
        Instance ins;
        ins.name = it["name"].get<std::string>();
        ins.type = it.value("type", "unknown");
        ins.width = it.value("width", 1.0);
        ins.height = it.value("height", 1.0);
        ins.x = 0.0; ins.y = 0.0;
        d.instances.push_back(ins);
    }
    for (auto &nt : j["nets"]) {
        Net n;
        n.name = nt["name"].get<std::string>();
        for (auto &p : nt["pins"]) {
            PinRef pr; pr.instance = p["instance"].get<std::string>(); pr.pin = p.value("pin", "");
            n.pins.push_back(pr);
        }
        d.nets.push_back(n);
    }
}

void initial_place_random(Design &d) {
    std::mt19937_64 rng(123456);
    std::uniform_real_distribution<double> ux(0.0, d.width);
    std::uniform_real_distribution<double> uy(0.0, d.height);
    for (auto &ins : d.instances) {
        ins.x = ux(rng);
        ins.y = uy(rng);
    }
}

// Compute smoothed HPWL using LSE approximation. Also compute gradients per-instance (flattened as pair vector)
double compute_smoothed_hpwl(const Design &d, double alpha, std::vector<std::pair<double,double>> &grad) {
    size_t n = d.instances.size();
    grad.assign(n, {0.0, 0.0});
    // map instance name to index
    std::unordered_map<std::string, size_t> idx;
    for (size_t i=0;i<n;i++) idx[d.instances[i].name] = i;

    double total = 0.0;
    for (const auto &net : d.nets) {
        // collect pin coords
        std::vector<double> xs, ys; xs.reserve(net.pins.size()); ys.reserve(net.pins.size());
        std::vector<size_t> indices;
        for (auto &p : net.pins) {
            auto it = idx.find(p.instance);
            if (it==idx.end()) continue;
            size_t id = it->second; indices.push_back(id);
            xs.push_back(d.instances[id].x);
            ys.push_back(d.instances[id].y);
        }
        if (xs.empty()) continue;
        // LSE for max and -min
        double max_x = *std::max_element(xs.begin(), xs.end());
        double min_x = *std::min_element(xs.begin(), xs.end());
        double max_y = *std::max_element(ys.begin(), ys.end());
        double min_y = *std::min_element(ys.begin(), ys.end());

        // compute LSE approximations
        double s_pos_x = 0.0, s_neg_x = 0.0; double s_pos_y = 0.0, s_neg_y = 0.0;
        std::vector<double> w_pos_x(xs.size()), w_neg_x(xs.size()), w_pos_y(ys.size()), w_neg_y(ys.size());
        for (size_t i=0;i<xs.size();i++) {
            double a = std::exp(alpha * (xs[i] - max_x));
            double b = std::exp(-alpha * (xs[i] - min_x));
            w_pos_x[i] = a; w_neg_x[i] = b; s_pos_x += a; s_neg_x += b;
            double c = std::exp(alpha * (ys[i] - max_y));
            double d2 = std::exp(-alpha * (ys[i] - min_y));
            w_pos_y[i] = c; w_neg_y[i] = d2; s_pos_y += c; s_neg_y += d2;
        }
        double lse_x = (1.0/alpha) * (std::log(s_pos_x) - std::log(s_neg_x) + max_x - min_x);
        double lse_y = (1.0/alpha) * (std::log(s_pos_y) - std::log(s_neg_y) + max_y - min_y);
        total += lse_x + lse_y;

        // gradients (chain rule)
        for (size_t i=0;i<xs.size();i++) {
            size_t id = indices[i];
            double d_ldx = (1.0/alpha) * ( (alpha * w_pos_x[i] / s_pos_x) - (-alpha * w_neg_x[i] / s_neg_x) );
            double d_ldy = (1.0/alpha) * ( (alpha * w_pos_y[i] / s_pos_y) - (-alpha * w_neg_y[i] / s_neg_y) );
            grad[id].first += d_ldx;
            grad[id].second += d_ldy;
        }
    }
    return total;
}

void write_placement_csv(const Design &d, const std::string &out_path) {
    std::ofstream ofs(out_path);
    ofs << "name,x,y\n";
    for (const auto &ins : d.instances) {
        ofs << ins.name << "," << ins.x << "," << ins.y << "\n";
    }
}

void run_optimizer(Design &d, int iterations, double alpha, double lambda_density, double gamma_ml) {
    size_t n = d.instances.size();
    std::vector<std::pair<double,double>> grad;
    double lr = 1.0;
    for (int it=0; it<iterations; ++it) {
        double wl = compute_smoothed_hpwl(d, alpha, grad);
        // simple gradient descent step
        for (size_t i=0;i<n;i++) {
            d.instances[i].x -= lr * grad[i].first;
            d.instances[i].y -= lr * grad[i].second;
            // clamp
            if (d.instances[i].x < 0) d.instances[i].x = 0;
            if (d.instances[i].x > d.width) d.instances[i].x = d.width;
            if (d.instances[i].y < 0) d.instances[i].y = 0;
            if (d.instances[i].y > d.height) d.instances[i].y = d.height;
        }
        if (it % 10 == 0) std::cout << "Iter " << it << ": WL=" << wl << "\n";
    }
}
