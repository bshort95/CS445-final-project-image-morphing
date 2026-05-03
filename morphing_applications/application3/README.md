# Application 3: Expression Transfer

This application transfers facial expression motion from one face image to another using Thin Plate Spline (TPS) warping.

The user first selects a square face box for each image. Landmarks are then clicked inside the face region. The expression displacement is computed in normalized face-box coordinates, so the faces do not need to appear at the same position or scale in the original photos.

## Input Images

Place the images in this folder:

```text
morphing-applications/application3/
```

For the simple two-image demo, use:

```text
app1.jpg    target neutral face
app2.jpg    driver expression face
```

In this mode, `app1.jpg` is reused as the driver neutral image. This means we transfer the landmark movement from `app1 -> app2` back onto `app1`.

## Run Interactive Demo

Run this command from the repository root:

```powershell
cd C:\UIUC\cs445\final_project\CS445-final-project-image-morphing

python morphing-applications\application3\expression_transfer.py `
  --target-neutral morphing-applications\application3\app1.jpg `
  --driver-neutral morphing-applications\application3\app1.jpg `
  --driver-expression morphing-applications\application3\app2.jpg `
  --interactive `
  --reuse-target-as-driver-neutral `
  --strength 1.0 `
  --max-display-width 900 `
  --max-display-height 650 `
  --save-clicked-prefix morphing-applications\application3\points\app_demo
```

If `python` is not available in PowerShell on this machine, use the project runtime workaround:

```powershell
$env:PYTHONPATH='C:\UIUC\cs445\.venv\Lib\site-packages'
C:\Users\kenzh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe morphing-applications\application3\expression_transfer.py `
  --target-neutral morphing-applications\application3\app1.jpg `
  --driver-neutral morphing-applications\application3\app1.jpg `
  --driver-expression morphing-applications\application3\app2.jpg `
  --interactive `
  --reuse-target-as-driver-neutral `
  --strength 1.0 `
  --max-display-width 900 `
  --max-display-height 650 `
  --save-clicked-prefix morphing-applications\application3\points\app_demo
```

## Manual Selection Steps

1. Draw a square box around the face in `app1.jpg`, then press `Enter`.
2. Draw a square box around the face in `app2.jpg`, then press `Enter`.
3. Click landmarks on `app1.jpg`, then press `Enter`.
4. Click the same landmarks in the same order on `app2.jpg`, then press `Enter`.

Recommended landmarks:

```text
left eye corner, right eye corner, eyebrow points, nose tip,
left mouth corner, right mouth corner, upper lip, lower lip, chin
```

Useful keys:

```text
u        undo last landmark point
Enter    finish current image
Esc      finish current image
r        reset the face box while selecting a box
```

## Run Again With Saved Points

After the interactive run, the selected boxes and landmarks are saved under:

```text
morphing-applications/application3/points/
```

Run again without clicking:

```powershell
python morphing-applications\application3\expression_transfer.py `
  --target-neutral morphing-applications\application3\app1.jpg `
  --driver-neutral morphing-applications\application3\app1.jpg `
  --driver-expression morphing-applications\application3\app2.jpg `
  --target-points morphing-applications\application3\points\app_demo_target_neutral.json `
  --driver-expression-points morphing-applications\application3\points\app_demo_driver_expression.json `
  --target-box morphing-applications\application3\points\app_demo_target_box.json `
  --driver-expression-box morphing-applications\application3\points\app_demo_driver_expression_box.json `
  --reuse-target-as-driver-neutral `
  --strength 1.0
```

## Outputs

Results are saved to:

```text
morphing-applications/application3/outputs/
```

Generated files:

```text
expression_transfer.jpg              final blended expression-transfer result
expression_transfer_full_warp.jpg    full TPS warp without face-region blending
expression_transfer_difference.jpg   amplified visualization of changed pixels
expression_motion.jpg                landmark motion arrows
expression_transfer_comparison.jpg   side-by-side comparison figure
```

## Notes

For best results, use two images where the face identity and pose are similar but the expression is different. If the output changes too much, reduce `--strength` to `0.5`. If the output barely changes, increase it to `1.5`.
