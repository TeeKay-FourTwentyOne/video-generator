// Audited whisper.cpp v1.9.5 bridge: retain raw and original-audio token times.
// Input is explicitly resampled mono float32 little-endian audio at 16000 Hz.
#include "whisper.h"
#include "json.hpp"
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <vector>
using nlohmann::json;

static std::string hex(const char * text) {
    static const char digits[] = "0123456789abcdef";
    std::string result;
    for (const unsigned char * p = reinterpret_cast<const unsigned char *>(text); *p; ++p) {
        result += digits[*p >> 4]; result += digits[*p & 15];
    }
    return result;
}

int main(int argc, char ** argv) {
    try {
        if (argc != 3) throw std::runtime_error("Expected private request and output paths");
        std::ifstream input(argv[1]); const auto r = json::parse(input);
        const auto s = r.at("settings");
        std::ifstream audio(r.at("audioFile").get<std::string>(), std::ios::binary | std::ios::ate);
        const auto bytes = audio.tellg();
        if (bytes <= 0 || bytes % 4 != 0 || bytes / 4 > std::numeric_limits<int>::max())
            throw std::runtime_error("Invalid mono float32 input");
        std::vector<float> pcm(static_cast<size_t>(bytes) / 4);
        audio.seekg(0); audio.read(reinterpret_cast<char *>(pcm.data()), bytes);
        if (!audio) throw std::runtime_error("Truncated audio input");
        auto cp = whisper_context_default_params(); cp.use_gpu = false;
        const std::string model = s.at("modelFile"), vad = s.at("vadModelFile"), language = s.value("language", "auto");
        std::unique_ptr<whisper_context, decltype(&whisper_free)> ctx(
            whisper_init_from_file_with_params(model.c_str(), cp), whisper_free);
        if (!ctx) throw std::runtime_error("Whisper initialization failed");
        auto p = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
        p.n_threads = r.at("threads"); p.language = language.c_str();
        p.print_progress = p.print_realtime = p.print_timestamps = p.print_special = false;
        p.token_timestamps = true; p.no_context = true; p.temperature = 0.0f;
        p.temperature_inc = 0.0f; // deterministic decoding; no temperature fallback
        p.vad = true; p.vad_model_path = vad.c_str();
        p.vad_params.threshold = s.at("vadThreshold");
        p.vad_params.min_speech_duration_ms = s.at("vadMinSpeechMs");
        p.vad_params.min_silence_duration_ms = s.at("vadMinSilenceMs");
        p.vad_params.speech_pad_ms = s.at("vadPadMs");
        p.vad_params.samples_overlap = s.at("vadOverlapSeconds");
        if (whisper_full(ctx.get(), p, pcm.data(), static_cast<int>(pcm.size())) != 0)
            throw std::runtime_error("Whisper/VAD inference failed");
        json out = {{"schemaVersion", 2}, {"contract", "whisper.cpp-original-time-v1"},
            {"sampleRate", 16000}, {"sampleCount", pcm.size()}, {"vad", json::array()}, {"transcription", json::array()},
            {"timing", {{"unit", "milliseconds"}, {"segments", "original-resampled-audio"},
                {"tokens", "original-resampled-audio"}, {"rawTokens", "vad-processed-audio"}}}};
        const int lang = whisper_full_n_vad_segments(ctx.get()) == 0 ? -1 : whisper_full_lang_id(ctx.get());
        out["language"] = {{"hypothesis", lang < 0 ? json(nullptr) : json(whisper_lang_str(lang))},
            {"confidence", nullptr}, {"interpretation", "Uncalibrated language hypothesis; music and short audio require review"}};
        for (int i = 0; i < whisper_full_n_vad_segments(ctx.get()); ++i)
            out["vad"].push_back({{"from", 10 * whisper_full_get_vad_segment_t0(ctx.get(), i)},
                {"to", 10 * whisper_full_get_vad_segment_t1(ctx.get(), i)}});
        for (int i = 0; i < whisper_full_n_segments(ctx.get()); ++i) {
            json segment = {{"text", whisper_full_get_segment_text(ctx.get(), i)},
                {"offsets", {{"from", 10 * whisper_full_get_segment_t0(ctx.get(), i)}, {"to", 10 * whisper_full_get_segment_t1(ctx.get(), i)}}},
                {"tokens", json::array()}};
            for (int j = 0; j < whisper_full_n_tokens(ctx.get(), i); ++j) {
                const auto token = whisper_full_get_token_data(ctx.get(), i, j);
                json t = {{"id", token.id}, {"bytesHex", hex(whisper_token_to_str(ctx.get(), token.id))},
                    {"p", token.p}, {"special", token.id >= whisper_token_eot(ctx.get())},
                    {"rawOffsets", {{"from", token.t0 * 10}, {"to", token.t1 * 10}}}, {"offsets", nullptr}};
                // Missing raw times stay missing. Mapping a sentinel would invent evidence.
                if (token.t0 >= 0 && token.t1 >= token.t0)
                    t["offsets"] = {{"from", 10 * whisper_full_get_token_t0(ctx.get(), i, j)},
                        {"to", 10 * whisper_full_get_token_t1(ctx.get(), i, j)}};
                segment["tokens"].push_back(t);
            }
            out["transcription"].push_back(segment);
        }
        std::ofstream output(argv[2]); output << out.dump(2) << '\n';
        if (!output) throw std::runtime_error("Cannot retain speech output");
    } catch (const std::exception & e) {
        std::cerr << e.what() << '\n'; return 1;
    }
}
