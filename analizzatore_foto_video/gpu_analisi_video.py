import argparse

# Aggiungi in fondo allo script prima del main()
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="Percorso video")
    parser.add_argument("--mode", type=str, default="faces", help="Modalità analisi")
    args = parser.parse_args()
    
    analyzer = VideoAnalyzerGPU(
        video_source=args.input,
        output_dir="output_frames"
    )
    analyzer.analyze_video(detection_mode=args.mode)