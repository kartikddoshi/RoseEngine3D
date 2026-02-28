use crate::generator::CutPath;
use std::fs::File;
use std::io::Write;
use std::path::Path;

/// Export cut paths as SVG
pub fn export_svg(
    paths: &[CutPath],
    file_path: &Path,
    width: f64,
    height: f64,
    stroke_width: f64,
) -> Result<(), String> {
    let mut file = File::create(file_path)
        .map_err(|e| format!("Failed to create SVG file: {}", e))?;

    // SVG header
    writeln!(
        file,
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n\
<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{}\" height=\"{}\" viewBox=\"{} {} {} {}\">\n\
  <rect width=\"100%\" height=\"100%\" fill=\"#000000\"/>\n\
  <g stroke=\"#b3924f\" fill=\"none\" stroke-width=\"{}\" stroke-linecap=\"round\" stroke-linejoin=\"round\">",
        width,
        height,
        -width / 2.0,
        -height / 2.0,
        width,
        height,
        stroke_width
    )
    .map_err(|e| format!("Failed to write SVG header: {}", e))?;

    // Draw each path
    for path in paths {
        if path.points.is_empty() {
            continue;
        }

        write!(file, "    <path d=\"M").map_err(|e| format!("Failed to write path: {}", e))?;

        for (i, point) in path.points.iter().enumerate() {
            if i == 0 {
                write!(file, " {:.2},{:.2}", point.x, -point.y)
                    .map_err(|e| format!("Failed to write point: {}", e))?;
            } else {
                write!(file, " L {:.2},{:.2}", point.x, -point.y)
                    .map_err(|e| format!("Failed to write point: {}", e))?;
            }
        }

        writeln!(file, "\" />").map_err(|e| format!("Failed to write path end: {}", e))?;
    }

    // SVG footer
    writeln!(file, "  </g>\n</svg>")
        .map_err(|e| format!("Failed to write SVG footer: {}", e))?;

    Ok(())
}
