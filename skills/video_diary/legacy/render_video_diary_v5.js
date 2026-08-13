const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

if (process.argv.length !== 5) {
  throw new Error("usage: node render_video_diary_v5.js <plan.json> <captions.json> <output.mp4>");
}

const cwd = process.cwd();
const plan = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const captions = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const output = path.resolve(process.argv[4]);
const outputDir = path.dirname(output);
const workDir = path.resolve(process.env.VIDEO_DIARY_WORK_DIR || "work/video_pilot/v5_generated");
const templateDir = path.resolve(process.env.VIDEO_DIARY_TEMPLATE_DIR || "outputs/video_pilot/templates");
fs.mkdirSync(outputDir, { recursive: true });
fs.mkdirSync(workDir, { recursive: true });
fs.mkdirSync(templateDir, { recursive: true });

const settings = {
  date: process.env.VIDEO_DIARY_DATE || "2026/07/23",
  day: process.env.VIDEO_DIARY_DAY || "Day13",
  outputAspectRatio: process.env.VIDEO_DIARY_OUTPUT_ASPECT_RATIO || "9:16",
  outputWidth: Number(process.env.VIDEO_DIARY_OUTPUT_WIDTH || 1080),
  outputHeight: Number(process.env.VIDEO_DIARY_OUTPUT_HEIGHT || 1920),
  aspectRatioSelection:
    process.env.VIDEO_DIARY_ASPECT_RATIO_SELECTION || "template_only_default",
  fps: 30,
  coverFrameCount: 2,
  subtitleFontFile: process.env.VIDEO_DIARY_FONT_SUBTITLE || "/System/Library/Fonts/STHeiti Medium.ttc",
  subtitleFontFamily: "Heiti SC Medium",
  subtitleFontSize: 68,
  subtitleOutline: 3.5,
  subtitleMarginBottom: Number(process.env.VIDEO_DIARY_OUTPUT_WIDTH || 1080) >
    Number(process.env.VIDEO_DIARY_OUTPUT_HEIGHT || 1920) ? 105 : 345,
  subtitleMaxWidth: Number(process.env.VIDEO_DIARY_OUTPUT_WIDTH || 1080) >
    Number(process.env.VIDEO_DIARY_OUTPUT_HEIGHT || 1920) ? 1600 : 880,
  coverTitleFontSize: 82,
  coverTitleMaxWidth: Number(process.env.VIDEO_DIARY_OUTPUT_WIDTH || 1080) >
    Number(process.env.VIDEO_DIARY_OUTPUT_HEIGHT || 1920) ? 1600 : 900,
  speed: Number(plan.speed ?? 1.0),
};
if (
  !Number.isInteger(settings.outputWidth) ||
  !Number.isInteger(settings.outputHeight) ||
  settings.outputWidth <= 0 ||
  settings.outputHeight <= 0
) {
  throw new Error("invalid resolved video-diary output dimensions");
}
if (!["16:9", "9:16"].includes(settings.outputAspectRatio)) {
  throw new Error("resolved output aspect ratio must be 16:9 or 9:16");
}
settings.isLandscape = settings.outputWidth > settings.outputHeight;
settings.coverDuration = settings.coverFrameCount / settings.fps;
const fonts = {
  subtitle: settings.subtitleFontFile,
  coverTitle: process.env.VIDEO_DIARY_FONT_COVER_TITLE || "/System/Library/Fonts/Supplemental/Songti.ttc",
  latinBold: process.env.VIDEO_DIARY_FONT_LATIN_BOLD || "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
  date: process.env.VIDEO_DIARY_FONT_DATE || "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
  day: process.env.VIDEO_DIARY_FONT_DAY || "/System/Library/Fonts/Supplemental/Arial Black.ttf",
  micro: process.env.VIDEO_DIARY_FONT_MICRO || "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf",
};
const imageTreatment = plan.image_treatment || {};
const audioTreatment = plan.audio_treatment || {};
const bgmMode = plan.bgm_mode || "default";

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd,
    encoding: "utf8",
    stdio: options.inherit ? "inherit" : "pipe",
  });
  if (result.status !== 0) {
    const detail = [result.stdout, result.stderr].filter(Boolean).join("\n");
    throw new Error(`${command} failed (${result.status})\n${detail}`);
  }
  return result;
}

function escapeFilterPath(value) {
  return value
    .replaceAll("\\", "\\\\")
    .replaceAll(":", "\\:")
    .replaceAll("'", "\\'");
}

function splitCoverTitle(value) {
  const explicitLines = plan.cover_title_lines;
  if (Array.isArray(explicitLines)) {
    const lines = explicitLines.map((line) => String(line).trim()).filter(Boolean);
    if (lines.length < 1 || lines.length > 2) {
      throw new Error("cover_title_lines must contain one or two non-empty lines");
    }
    return lines;
  }

  const title = String(value || "").trim();
  if (!title) throw new Error("plan.title is required for the two-frame cover");
  if (title.length <= 10) return [title];
  const midpoint = Math.ceil(title.length / 2);
  const lines = [title.slice(0, midpoint), title.slice(midpoint)];
  if (lines.some((line) => line.length > 12)) {
    throw new Error(
      "cover title is too long for two safe lines; provide plan.cover_title_lines",
    );
  }
  return lines;
}

function createTemplate(kind, outputPath) {
  const isCover = kind === "cover";
  const values = settings.isLandscape
    ? (isCover
      ? {
          recX: 56, recY: 30, recSize: 22,
          leftX: 55, rightX: 465, topY: 70, bottomY: 450, stroke: 7, cap: 54, cornerV: 54,
          mesY: 120, mesSize: 100,
          cnY: 240, cnSize: 100,
          diaryX: 195, diaryY: 414, diarySize: 16,
          dateRight: 1870, dateY: 50, dateSize: 82,
          dayRight: 1870, dayY: 130, daySize: 128,
          titleBaseY: 770,
          titleLineGap: 106,
          textOutline: 2,
          showMicroLabels: true,
          showCoverTitle: true,
        }
      : {
          leftX: 35, rightX: 290, topY: 28, bottomY: 250, stroke: 5, cap: 28, cornerV: 50,
          mesY: 48, mesSize: 65,
          cnY: 124, cnSize: 68,
          dateRight: 1880, dateY: 24, dateSize: 52,
          dayRight: 1880, dayY: 80, daySize: 80,
          textOutline: 3,
          showMicroLabels: false,
          showCoverTitle: false,
        })
    : (isCover
    ? {
        recX: 76, recY: 66, recSize: 22,
        leftX: 74, rightX: 417, topY: 124, bottomY: 445, stroke: 7, cap: 54, cornerV: 54,
        mesY: 174, mesSize: 100,
        cnY: 293, cnSize: 100,
        diaryX: 194, diaryY: 414, diarySize: 16,
        dateRight: 1000, dateY: 126, dateSize: 82,
        dayRight: 1015, dayY: 205, daySize: 128,
        titleBaseY: 1280,
        titleLineGap: 106,
        textOutline: 2,
        showMicroLabels: true,
        showCoverTitle: true,
      }
    : {
        leftX: 36, rightX: 318, topY: 64, bottomY: 314, stroke: 6, cap: 32, cornerV: 66,
        mesY: 98, mesSize: 92,
        cnY: 200, cnSize: 94,
        dateRight: 1040, dateY: 92, dateSize: 75,
        dayRight: 1040, dayY: 166, daySize: 118,
        textOutline: 3,
        showMicroLabels: false,
        showCoverTitle: false,
      });

  const mesText = path.join(workDir, `${kind}_mes.txt`);
  const cnText = path.join(workDir, `${kind}_cn.txt`);
  const dateText = path.join(workDir, `${kind}_date.txt`);
  const dayText = path.join(workDir, `${kind}_day.txt`);
  const recText = path.join(workDir, `${kind}_rec.txt`);
  const diaryText = path.join(workDir, `${kind}_diary.txt`);
  const titleLines = values.showCoverTitle ? splitCoverTitle(plan.title) : [];
  const titleTextPaths = titleLines.map(
    (_, index) => path.join(workDir, `${kind}_title_${index + 1}.txt`),
  );
  fs.writeFileSync(mesText, "MES\n");
  fs.writeFileSync(cnText, "日记\n");
  fs.writeFileSync(dateText, `${settings.date}\n`);
  fs.writeFileSync(dayText, `${settings.day}\n`);
  fs.writeFileSync(recText, "REC\n");
  fs.writeFileSync(diaryText, "Diary\n");
  if (values.showCoverTitle) {
    titleLines.forEach((line, index) => {
      fs.writeFileSync(titleTextPaths[index], `${line}\n`);
    });
  }

  const yellow = "0xFFF200@1";
  const white = "0xFFFFFF@1";
  const outline = "0x111111@1";
  const filters = [
    "format=rgba",
    `drawbox=x=${values.leftX}:y=${values.topY}:w=${values.stroke}:h=${values.cornerV}:color=${yellow}:t=fill`,
    `drawbox=x=${values.leftX}:y=${values.bottomY - values.cornerV}:w=${values.stroke}:h=${values.cornerV}:color=${yellow}:t=fill`,
    `drawbox=x=${values.leftX}:y=${values.topY}:w=${values.cap}:h=${values.stroke}:color=${yellow}:t=fill`,
    `drawbox=x=${values.leftX}:y=${values.bottomY - values.stroke}:w=${values.cap}:h=${values.stroke}:color=${yellow}:t=fill`,
    `drawbox=x=${values.rightX - values.stroke}:y=${values.topY}:w=${values.stroke}:h=${values.cornerV}:color=${yellow}:t=fill`,
    `drawbox=x=${values.rightX - values.stroke}:y=${values.bottomY - values.cornerV}:w=${values.stroke}:h=${values.cornerV}:color=${yellow}:t=fill`,
    `drawbox=x=${values.rightX - values.cap}:y=${values.topY}:w=${values.cap}:h=${values.stroke}:color=${yellow}:t=fill`,
    `drawbox=x=${values.rightX - values.cap}:y=${values.bottomY - values.stroke}:w=${values.cap}:h=${values.stroke}:color=${yellow}:t=fill`,
    `drawtext=fontfile='${escapeFilterPath(fonts.latinBold)}':textfile='${escapeFilterPath(mesText)}':x=${values.leftX}+((${values.rightX}-${values.leftX})-text_w)/2:y=${values.mesY}:fontsize=${values.mesSize}:fontcolor=${white}:borderw=${values.textOutline}:bordercolor=${outline}`,
    `drawtext=fontfile='${escapeFilterPath(fonts.subtitle)}':textfile='${escapeFilterPath(cnText)}':x=${values.leftX}+((${values.rightX}-${values.leftX})-text_w)/2-7:y=${values.cnY}:fontsize=${values.cnSize}:fontcolor=${white}:borderw=${values.textOutline}:bordercolor=${outline}`,
    `drawtext=fontfile='${escapeFilterPath(fonts.date)}':textfile='${escapeFilterPath(dateText)}':x=${values.dateRight}-text_w:y=${values.dateY}:fontsize=${values.dateSize}:fontcolor=${white}:borderw=${values.textOutline}:bordercolor=${outline}`,
    `drawtext=fontfile='${escapeFilterPath(fonts.day)}':textfile='${escapeFilterPath(dayText)}':x=${values.dayRight}-text_w:y=${values.dayY}:fontsize=${values.daySize}:fontcolor=${white}:borderw=${values.textOutline}:bordercolor=${outline}`,
    ...(values.showMicroLabels ? [
      `drawbox=x=${values.recX}:y=${values.recY + Math.round(values.recSize * 0.22)}:w=8:h=8:color=${yellow}:t=fill`,
      `drawtext=fontfile='${escapeFilterPath(fonts.micro)}':textfile='${escapeFilterPath(recText)}':x=${values.recX + 12}:y=${values.recY}:fontsize=${values.recSize}:fontcolor=${yellow}`,
      `drawtext=fontfile='${escapeFilterPath(fonts.date)}':textfile='${escapeFilterPath(diaryText)}':x=${values.diaryX}:y=${values.diaryY}:fontsize=${values.diarySize}:fontcolor=${yellow}`,
    ] : []),
    ...(values.showCoverTitle
      ? titleTextPaths.map(
          (titleTextPath, index) =>
            `drawtext=fontfile='${escapeFilterPath(fonts.coverTitle)}':textfile='${escapeFilterPath(titleTextPath)}':x=(w-text_w)/2:y=${values.titleBaseY + index * values.titleLineGap}:fontsize=${settings.coverTitleFontSize}:fontcolor=${white}:borderw=3:bordercolor=${outline}`,
        )
      : []),
    "colorkey=0x000000:0.01:0",
    "format=rgba",
  ];
  run("ffmpeg", [
    "-y", "-hide_banner", "-loglevel", "error",
    "-f", "lavfi", "-i",
    `color=c=black:s=${settings.outputWidth}x${settings.outputHeight}:r=30`,
    "-vf", filters.join(","),
    "-frames:v", "1", outputPath,
  ]);
}

function measureCaption(text, index) {
  const lines = String(text).split(/\\N|\n/u);
  if (lines.length > 2 || lines.some((line) => !line.trim())) {
    throw new Error(`caption ${index + 1} must contain one or two non-empty lines`);
  }
  const widths = lines.map((line, lineIndex) => {
    const stem = `${String(index + 1).padStart(3, "0")}_${lineIndex + 1}`;
    const textPath = path.join(workDir, `measure_${stem}.txt`);
    const imagePath = path.join(workDir, `measure_${stem}.png`);
    fs.writeFileSync(textPath, `${line}\n`);
    run("ffmpeg", [
      "-y", "-hide_banner", "-loglevel", "error",
      "-f", "lavfi", "-i", "color=c=black:s=1600x180",
      "-vf",
      `drawtext=fontfile='${settings.subtitleFontFile}':textfile='${escapeFilterPath(textPath)}':fontsize=${settings.subtitleFontSize}:fontcolor=white:borderw=4:bordercolor=white:x=20:y=20`,
      "-frames:v", "1", imagePath,
    ]);
    const result = run("ffmpeg", [
      "-hide_banner", "-loglevel", "info",
      "-loop", "1", "-i", imagePath,
      "-vf", "cropdetect=limit=0.01:round=1:reset=1",
      "-frames:v", "5", "-f", "null", "-",
    ]);
    const matches = [...result.stderr.matchAll(/crop=(\d+):(\d+):(-?\d+):(-?\d+)/g)];
    if (matches.length === 0) {
      throw new Error(`unable to measure caption ${index + 1}, line ${lineIndex + 1}: ${line}`);
    }
    return Number(matches.at(-1)[1]);
  });
  const width = Math.max(...widths);
  return {
    index: index + 1,
    text,
    line_count: lines.length,
    line_widths: widths,
    width,
    max_width: settings.subtitleMaxWidth,
    passed: width <= settings.subtitleMaxWidth,
  };
}

function mergeCuts(cuts) {
  const sorted = cuts.map(({ start, end }) => ({ start, end })).sort((a, b) => a.start - b.start);
  const merged = [];
  for (const cut of sorted) {
    const last = merged.at(-1);
    if (!last || cut.start > last.end) merged.push({ ...cut });
    else last.end = Math.max(last.end, cut.end);
  }
  return merged;
}

const cuts = mergeCuts(plan.remove);
const keep = [];
let cursor = 0;
for (const cut of cuts) {
  if (cut.start > cursor) keep.push({ start: cursor, end: cut.start });
  cursor = Math.max(cursor, cut.end);
}
if (cursor < plan.source_duration_seconds) keep.push({ start: cursor, end: plan.source_duration_seconds });

function removedBefore(time) {
  let removed = 0;
  for (const cut of cuts) {
    if (time >= cut.end) removed += cut.end - cut.start;
    else if (time > cut.start) removed += time - cut.start;
  }
  return removed;
}

function outputTime(rawTime) {
  return (rawTime - removedBefore(rawTime)) / settings.speed;
}

function assTime(seconds) {
  const totalCentis = Math.max(0, Math.round(seconds * 100));
  const hours = Math.floor(totalCentis / 360000);
  const minutes = Math.floor((totalCentis % 360000) / 6000);
  const secs = Math.floor((totalCentis % 6000) / 100);
  const centis = totalCentis % 100;
  return `${hours}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}.${String(centis).padStart(2, "0")}`;
}

function escapeAss(text) {
  return text
    .replaceAll("{", "\\{")
    .replaceAll("}", "\\}")
    .replaceAll("\n", "\\N");
}

const aspectSuffix = settings.outputAspectRatio.replace(":", "x");
const templateSuffix = settings.isLandscape ? `_${aspectSuffix}` : "";
const coverPath = path.join(
  templateDir,
  `video_diary_cover_2026-07-23_day13_v5${templateSuffix}.png`,
);
const headerPath = path.join(
  templateDir,
  `video_diary_header_2026-07-23_day13_v5${templateSuffix}.png`,
);
createTemplate("cover", coverPath);
createTemplate("header", headerPath);
if (process.env.VIDEO_DIARY_TEMPLATE_ONLY === "1") process.exit(0);

const widthReport = captions.map((caption, index) => measureCaption(caption.text, index));
const overflow = widthReport.filter((item) => !item.passed);
const widthReportPath = path.resolve(process.env.VIDEO_DIARY_WIDTH_REPORT || "outputs/video_pilot/subtitle_width_report.json");
fs.mkdirSync(path.dirname(widthReportPath), { recursive: true });
fs.writeFileSync(widthReportPath, `${JSON.stringify({
  font_file: settings.subtitleFontFile,
  font_size: settings.subtitleFontSize,
  maximum_width: settings.subtitleMaxWidth,
  caption_count: captions.length,
  overflow_count: overflow.length,
  captions: widthReport,
}, null, 2)}\n`);
if (overflow.length > 0) {
  throw new Error(`subtitle overflow: ${overflow.map((item) => `#${item.index} ${item.width}px`).join(", ")}`);
}

const assPath = output.replace(/\.mp4$/i, ".ass");
const encodedOutput = `${output}.encoded.mp4`;
const assLines = [
  "[Script Info]",
  "ScriptType: v4.00+",
  `PlayResX: ${settings.outputWidth}`,
  `PlayResY: ${settings.outputHeight}`,
  "WrapStyle: 2",
  "ScaledBorderAndShadow: yes",
  "",
  "[V4+ Styles]",
  "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
  `Style: Subtitle,${settings.subtitleFontFamily},${settings.subtitleFontSize},&H00FFFFFF,&H00FFFFFF,&H00111111,&H59000000,0,0,0,0,100,100,0,0,1,${settings.subtitleOutline},1.5,2,100,100,${settings.subtitleMarginBottom},1`,
  "",
  "[Events]",
  "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
];
for (const caption of captions) {
  const start = Math.max(settings.coverDuration, outputTime(caption.start));
  const end = outputTime(caption.end);
  if (end <= start) throw new Error(`invalid caption duration: ${caption.text}`);
  assLines.push(`Dialogue: 0,${assTime(start)},${assTime(end)},Subtitle,,0,0,0,,${escapeAss(caption.text)}`);
}
fs.writeFileSync(assPath, `${assLines.join("\n")}\n`);

const chains = [];
const concatInputs = [];
for (let index = 0; index < keep.length; index++) {
  const segment = keep[index];
  chains.push(`[0:v]trim=start=${segment.start}:end=${segment.end},setpts=PTS-STARTPTS[v${index}]`);
  chains.push(`[0:a]atrim=start=${segment.start}:end=${segment.end},asetpts=PTS-STARTPTS[a${index}]`);
  concatInputs.push(`[v${index}][a${index}]`);
}
chains.push(`${concatInputs.join("")}concat=n=${keep.length}:v=1:a=1[vcat][acat]`);
const videoFilters = [`setpts=PTS/${settings.speed}`];
if ((plan.input_color_transform || "hlg_to_sdr") === "hlg_to_sdr") {
  videoFilters.push(
    "zscale=t=linear:npl=100",
    "format=gbrpf32le",
    "zscale=p=bt709",
    "tonemap=hable:desat=0",
    "zscale=t=bt709:m=bt709:r=tv",
  );
}
videoFilters.push("format=yuv420p");
if (imageTreatment.mode === "dark") {
  videoFilters.push("eq=brightness=0.025:gamma=1.015");
} else if (imageTreatment.mode === "low_contrast") {
  videoFilters.push("eq=contrast=1.035:saturation=1.01");
} else if (imageTreatment.mode === "noisy") {
  videoFilters.push("hqdn3d=0.55:0.45:1.10:0.90");
} else if (imageTreatment.mode !== "none") {
  throw new Error(`unsupported image_treatment.mode: ${imageTreatment.mode}`);
}
videoFilters.push(
  `scale=${settings.outputWidth}:${settings.outputHeight}:force_original_aspect_ratio=decrease`,
  `pad=${settings.outputWidth}:${settings.outputHeight}:(ow-iw)/2:(oh-ih)/2:black`,
  "setsar=1",
  `fps=${settings.fps}`,
);
chains.push(`[vcat]${videoFilters.join(",")}[vbase]`);

const voiceFilters = [`atempo=${settings.speed}`];
if (audioTreatment.class === "B" || audioTreatment.class === "C") {
  voiceFilters.push("afftdn=nr=8:nf=-38:tn=1");
} else if (audioTreatment.class === "D") {
  throw new Error("audio class D requires manual review; automatic render is blocked");
} else if (audioTreatment.class !== "A") {
  throw new Error(`unsupported audio_treatment.class: ${audioTreatment.class}`);
}
voiceFilters.push(
  "loudnorm=I=-16:LRA=7:TP=-1",
  "alimiter=limit=0.891:attack=5:release=50",
  "asetpts=PTS-STARTPTS",
);

const outputDuration = keep.reduce(
  (total, segment) => total + segment.end - segment.start,
  0,
) / settings.speed;
let bgmPath = "";
if (bgmMode === "default") {
  const provider = process.env.VIDEO_DIARY_DEFAULT_BGM_PROVIDER || "local";
  if (provider === "jianying") {
    throw new Error(
      "default BGM is a Jianying library track and must be applied inside Jianying; standalone cache redistribution and FFmpeg mixing are blocked",
    );
  }
  bgmPath = process.env.VIDEO_DIARY_DEFAULT_BGM_PATH || "";
  if (process.env.VIDEO_DIARY_DEFAULT_BGM_AUTHORIZATION !== "CONFIRMED") {
    throw new Error(
      "default BGM is blocked: authorization_status must be CONFIRMED",
    );
  }
} else if (bgmMode === "custom") {
  bgmPath = String(plan.bgm_path || "");
  if (plan.bgm_authorization_status !== "CONFIRMED") {
    throw new Error(
      "custom BGM is blocked: bgm_authorization_status must be CONFIRMED",
    );
  }
} else if (bgmMode !== "off") {
  throw new Error(`unsupported bgm_mode: ${bgmMode}`);
}
if (bgmPath && !fs.existsSync(bgmPath)) {
  throw new Error(`BGM file not found: ${bgmPath}`);
}

if (bgmPath) {
  const probe = run("ffprobe", [
    "-v", "error",
    "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1",
    bgmPath,
  ]);
  const bgmDuration = Number(probe.stdout.trim());
  if (!Number.isFinite(bgmDuration) || bgmDuration + 0.05 < outputDuration) {
    throw new Error(
      `BGM is shorter than output (${bgmDuration}s < ${outputDuration}s); hard looping is forbidden`,
    );
  }
  const fadeOut = Math.max(0, outputDuration - 1);
  chains.push(`[acat]${voiceFilters.join(",")}[voice]`);
  chains.push(
    `[3:a]atrim=duration=${outputDuration},asetpts=PTS-STARTPTS,loudnorm=I=-33:LRA=9:TP=-3,afade=t=in:st=0:d=1,afade=t=out:st=${fadeOut}:d=1[bgm]`,
  );
  chains.push("[voice]asplit=2[voice_main][voice_sidechain]");
  chains.push(
    "[bgm][voice_sidechain]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[bgm_ducked]",
  );
  chains.push(
    "[voice_main][bgm_ducked]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.891:attack=5:release=50[aout]",
  );
} else {
  chains.push(`[acat]${voiceFilters.join(",")}[aout]`);
}
chains.push(`[1:v]format=rgba[cover]`);
chains.push(`[2:v]format=rgba[header]`);
chains.push(`[vbase][cover]overlay=0:0:enable='lt(n,${settings.coverFrameCount})'[vcover]`);
chains.push(`[vcover][header]overlay=0:0:enable='gte(n,${settings.coverFrameCount})'[vtemplated]`);
chains.push(`[vtemplated]subtitles='${escapeFilterPath(assPath)}'[vout]`);

const ffmpegArgs = [
  "-y", "-hide_banner",
  "-i", plan.source,
  "-loop", "1", "-framerate", "30", "-i", coverPath,
  "-loop", "1", "-framerate", "30", "-i", headerPath,
  ...(bgmPath ? ["-i", bgmPath] : []),
  "-filter_complex", chains.join(";"),
  "-map", "[vout]", "-map", "[aout]",
  "-map_metadata", "-1",
  "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
  "-profile:v", "high", "-pix_fmt", "yuv420p",
  "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
  "-movflags", "+faststart",
  "-shortest",
  encodedOutput,
];
run("ffmpeg", ffmpegArgs, { inherit: true });
run("ffmpeg", [
  "-y", "-hide_banner", "-loglevel", "error",
  "-display_rotation:v:0", "0",
  "-i", encodedOutput,
  "-map", "0",
  "-c", "copy",
  "-movflags", "+faststart",
  output,
]);
fs.unlinkSync(encodedOutput);
