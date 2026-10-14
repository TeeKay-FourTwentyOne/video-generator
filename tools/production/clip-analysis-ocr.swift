import Foundation
import Vision
import ImageIO

// Compiled explicitly by analysis setup-ocr; runs inside a network-denied sandbox.
do {
    guard CommandLine.arguments.count == 3 else { throw NSError(domain: "ClipOCR", code: 1) }
    let data = try Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1]))
    let input = try JSONSerialization.jsonObject(with: data) as! [String: Any]
    let samples = input["samples"] as! [[String: Any]]
    var observations = [[String: Any]]()
    for sample in samples {
        let request = VNRecognizeTextRequest()
        request.revision = VNRecognizeTextRequestRevision3
        request.recognitionLevel = .accurate
        request.usesLanguageCorrection = false
        if #available(macOS 13.0, *) { request.automaticallyDetectsLanguage = true }
        let handler = VNImageRequestHandler(url: URL(fileURLWithPath: sample["path"] as! String), options: [:])
        try handler.perform([request])
        for found in request.results ?? [] {
            guard let candidate = found.topCandidates(1).first else { continue }
            let box = found.boundingBox
            observations.append([
                "sourceSha256": input["sourceSha256"]!, "evidenceType": "model-observation",
                "streamIndex": sample["streamIndex"]!, "startSeconds": sample["seconds"]!, "endSeconds": sample["seconds"]!,
                "frameIndices": [sample["frameIndex"]!], "pts": sample["pts"]!, "timeBase": sample["timeBase"]!,
                "text": candidate.string, "originalText": candidate.string,
                "normalizedText": candidate.string.precomposedStringWithCompatibilityMapping,
                "boxNormalized": [box.origin.x, box.origin.y, box.size.width, box.size.height], "boxOrigin": "bottom-left",
                "confidence": ["source": "Apple Vision revision 3", "value": candidate.confidence, "interpretation": "uncalibrated model score"]
            ])
        }
    }
    let result: [String: Any] = ["schemaVersion": 1, "observations": observations]
    let output = try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys])
    try output.write(to: URL(fileURLWithPath: CommandLine.arguments[2]), options: .withoutOverwriting)
} catch {
    FileHandle.standardError.write(Data("Native OCR failed; no negative observation inferred.\n".utf8))
    exit(1)
}
