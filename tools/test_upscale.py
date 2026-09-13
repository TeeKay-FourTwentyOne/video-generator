"""Regression tests for exact-size video upscaling and unchanged audio."""
import importlib.util
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("upscale", Path(__file__).with_name("upscale.py"))
upscale = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upscale)


class UpscaleTests(unittest.TestCase):
    def test_actual_wrapper_models(self):
        self.assertEqual(upscale.MODELS[0]["wrapper_id"], 4)
        self.assertEqual(upscale.MODELS[0]["native_scale"], 4)
        self.assertEqual(upscale.MODELS[1]["wrapper_id"], 0)
        self.assertEqual(upscale.MODELS[1]["native_scale"], 2)

    def test_encoder_preserves_audio_and_does_not_overwrite(self):
        cmd = upscale.encode_command(Path("frames"), Path("source.mp4"), Path("4k.mp4"), "24/1", 16)
        self.assertEqual(cmd[cmd.index("-c:a") + 1], "copy")
        self.assertIn("1:a?", cmd)
        self.assertIn("+faststart", cmd)
        self.assertIn("-n", cmd)
        self.assertNotIn("-y", cmd)

    def test_probe_uses_video_duration_not_longer_audio(self):
        data = {"streams": [{"codec_type": "audio"}, {
            "codec_type": "video", "width": 1920, "height": 1080,
            "r_frame_rate": "24/1", "avg_frame_rate": "24/1", "duration": "24",
        }], "format": {"duration": "25"}}
        with patch.object(upscale, "probe", return_value=data):
            self.assertEqual(upscale.get_video_info("x"), (1920, 1080, "24/1", 24.0))
            data["streams"][1]["avg_frame_rate"] = "23/1"
            with self.assertRaisesRegex(ValueError, "constant-frame-rate"):
                upscale.get_video_info("x")

    def test_failed_command_is_not_silently_accepted(self):
        with self.assertRaisesRegex(RuntimeError, "failed"):
            upscale.run_checked([sys.executable, "-c", "raise SystemExit(1)"])

    def test_frame_and_audio_preservation_integration(self):
        # Fake only the expensive neural network. Exercise real extraction, sizing,
        # encoding, muxing and ffprobe on both documented model paths.
        from PIL import Image

        class FakeModel:
            def __init__(self, gpuid, model, tilesize):
                self.scale = 4 if model == 4 else 2

            def process_pil(self, image):
                return image.resize((image.width * self.scale, image.height * self.scale), Image.Resampling.NEAREST)

        def audio_hash(path):
            return subprocess.check_output([
                "ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0",
                "-c:a", "copy", "-f", "hash", "-hash", "sha256", "-",
            ])

        with tempfile.TemporaryDirectory(prefix="test-upscale-") as folder:
            src = Path(folder) / "input.mp4"
            upscale.run_checked([
                "ffmpeg", "-v", "error", "-n", "-f", "lavfi", "-i", "testsrc2=s=32x16:r=24:d=0.25",
                "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=0.25",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(src),
            ])
            original = src.read_bytes()
            for model_id in [0, 1]:
                out = Path(folder) / f"output-{model_id}.mp4"
                argv = ["upscale.py", str(src), str(out), "--scale", "2", "--model", str(model_id)]
                with patch.dict(sys.modules, {"realesrgan_ncnn_py": types.SimpleNamespace(Realesrgan=FakeModel)}), patch.object(sys, "argv", argv):
                    upscale.main()
                info = upscale.probe(out)
                video = info["streams"][0]
                self.assertEqual((video["width"], video["height"], video["nb_frames"]), (64, 32, "6"))
                self.assertEqual(audio_hash(src), audio_hash(out))
                self.assertEqual(src.read_bytes(), original)
                with patch.object(sys, "argv", argv), self.assertRaises(SystemExit):
                    upscale.main()


if __name__ == "__main__":
    unittest.main()
