import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const PUBLICATION_URL =
  "https://www.ksh.hu/s/kiserleti-statisztika/kiadvanyok/a-magyar-lakasallomany-primerenergia-igenyenek-becslese/";
const METHODOLOGY_URL = `${PUBLICATION_URL}modszertan`;
const SOURCE_ID = "SRC-B02-KSH-ENERGY-2025";
const METHOD_SOURCE_ID = "SRC-B02-KSH-ENERGY-METHOD-2025";

const EXPECTED_TITLES = {
  energyClass: "A lakásállomány megoszlása az energiaosztályokban, 2022",
  meanByPeriod:
    "Átlagos energiaigény az építés időszaka szerint, épülettípusonként, ÉKM, 2022",
  multiDistribution:
    "Többlakásos épületek lakásainak eloszlása energiaigényük szerint, építési időszakonként, ÉKM, 2022",
  familyDistribution:
    "Családi házak eloszlása energiaigényük szerint, építési időszakonként, ÉKM",
};

function parseArgs(argv) {
  const result = {
    outputDir: "data/processed/b02",
    retrievedAt: new Date().toISOString().slice(0, 10),
  };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--output-dir") result.outputDir = argv[++index];
    else if (argument === "--retrieved-at") result.retrievedAt = argv[++index];
    else throw new Error(`unknown argument: ${argument}`);
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(result.retrievedAt)) {
    throw new Error(`invalid --retrieved-at: ${result.retrievedAt}`);
  }
  return result;
}

function sha256(text) {
  return crypto.createHash("sha256").update(text, "utf8").digest("hex");
}

function decodeHtml(value) {
  return value
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;|&#160;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'")
    .replace(/\s+/g, " ")
    .trim();
}

function unescapeJsString(value) {
  return value
    .replace(/\\u([0-9a-f]{4})/gi, (_, code) => String.fromCharCode(Number.parseInt(code, 16)))
    .replace(/\\x([0-9a-f]{2})/gi, (_, code) => String.fromCharCode(Number.parseInt(code, 16)))
    .replace(/\\'/g, "'")
    .replace(/\\n/g, "\n")
    .replace(/\\\\/g, "\\");
}

function extractBalanced(text, startIndex, open, close) {
  if (text[startIndex] !== open) throw new Error(`expected ${open} at ${startIndex}`);
  let depth = 0;
  let quote = null;
  let escaped = false;
  for (let index = startIndex; index < text.length; index += 1) {
    const character = text[index];
    if (quote) {
      if (escaped) escaped = false;
      else if (character === "\\") escaped = true;
      else if (character === quote) quote = null;
      continue;
    }
    if (character === "'" || character === '"' || character === "`") {
      quote = character;
      continue;
    }
    if (character === open) depth += 1;
    else if (character === close) {
      depth -= 1;
      if (depth === 0) return text.slice(startIndex, index + 1);
    }
  }
  throw new Error(`unterminated ${open}${close} block`);
}

function parseStringArray(arrayText) {
  const values = [];
  for (const match of arrayText.matchAll(/'((?:\\.|[^'])*)'/g)) {
    values.push(unescapeJsString(match[1]));
  }
  return values;
}

function parseNumberArray(arrayText) {
  const inner = arrayText.slice(1, -1).trim();
  if (!inner) return [];
  return inner.split(",").map((rawValue) => {
    const value = rawValue.trim();
    if (value === "null") return null;
    if (!/^-?\d+(?:\.\d+)?$/.test(value)) {
      throw new Error(`non-numeric chart value: ${value}`);
    }
    return Number(value);
  });
}

function extractCharts(html) {
  const pattern = /createChart\('([^']+)',\s*\(\{([\s\S]*?)\}\)\);/g;
  const charts = [];
  for (const match of html.matchAll(pattern)) {
    const body = match[2];
    const titleMatch = body.match(/title:\s*\{\s*text:\s*'((?:\\.|[^'])*)'/);
    if (!titleMatch) continue;
    const categoriesMarker = body.indexOf("categories:");
    let categories = [];
    if (categoriesMarker >= 0) {
      const start = body.indexOf("[", categoriesMarker);
      categories = parseStringArray(extractBalanced(body, start, "[", "]"));
    }
    const seriesMarker = body.indexOf("series:");
    if (seriesMarker < 0) throw new Error(`chart has no series: ${titleMatch[1]}`);
    const seriesStart = body.indexOf("[", seriesMarker);
    const seriesText = extractBalanced(body, seriesStart, "[", "]");
    const series = [];
    let cursor = 1;
    while (cursor < seriesText.length - 1) {
      const objectStart = seriesText.indexOf("{", cursor);
      if (objectStart < 0) break;
      const objectText = extractBalanced(seriesText, objectStart, "{", "}");
      const nameMatch = objectText.match(/name:\s*'((?:\\.|[^'])*)'/);
      const dataMarker = objectText.indexOf("data:");
      if (nameMatch && dataMarker >= 0) {
        const dataStart = objectText.indexOf("[", dataMarker);
        if (dataStart < 0) {
          cursor = objectStart + objectText.length;
          continue;
        }
        const dataText = extractBalanced(objectText, dataStart, "[", "]");
        if (!dataText.includes("{")) {
          series.push({
            name: unescapeJsString(nameMatch[1]),
            data: parseNumberArray(dataText),
          });
        }
      }
      cursor = objectStart + objectText.length;
    }
    charts.push({
      title: unescapeJsString(titleMatch[1]),
      categories,
      series,
    });
  }
  return charts;
}

function parseMethodologyControls(html) {
  const tables = [...html.matchAll(/<table\b[\s\S]*?<\/table>/gi)].map((match) => match[0]);
  if (tables.length === 0) throw new Error("methodology page has no tables");
  const rows = [...tables[0].matchAll(/<tr\b[\s\S]*?<\/tr>/gi)].map((match) =>
    [...match[0].matchAll(/<(?:th|td)\b[^>]*>([\s\S]*?)<\/(?:th|td)>/gi)].map((cell) =>
      decodeHtml(cell[1]),
    ),
  );
  const total = rows.find((row) => row[0] === "Összesen");
  if (!total || total.length !== 6) throw new Error(`unexpected methodology total row: ${total}`);
  const parseHuNumber = (value) => Number(value.replace(/\s/g, "").replace(",", "."));
  return {
    censusDwellingUniverse: parseHuNumber(total[1]),
    linkedCertificates: parseHuNumber(total[3]),
    publishedLinkRatePercent: parseHuNumber(total[5]),
  };
}

function csvEscape(value) {
  if (value === null || value === undefined) return "";
  const text = String(value);
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function toCsv(headers, rows) {
  return `${[headers, ...rows].map((row) => row.map(csvEscape).join(",")).join("\n")}\n`;
}

function requireChart(charts, title) {
  const chart = charts.find((candidate) => candidate.title === title);
  if (!chart) throw new Error(`missing expected chart: ${title}`);
  return chart;
}

function sum(values) {
  return values.reduce((total, value) => total + (value ?? 0), 0);
}

const { outputDir, retrievedAt } = parseArgs(process.argv.slice(2));
const [publicationResponse, methodologyResponse] = await Promise.all([
  fetch(PUBLICATION_URL),
  fetch(METHODOLOGY_URL),
]);
if (!publicationResponse.ok) throw new Error(`publication HTTP ${publicationResponse.status}`);
if (!methodologyResponse.ok) throw new Error(`methodology HTTP ${methodologyResponse.status}`);
const publicationHtml = await publicationResponse.text();
const methodologyHtml = await methodologyResponse.text();
const publicationSha256 = sha256(publicationHtml);
const methodologySha256 = sha256(methodologyHtml);

const charts = extractCharts(publicationHtml);
const energyClass = requireChart(charts, EXPECTED_TITLES.energyClass);
const means = requireChart(charts, EXPECTED_TITLES.meanByPeriod);
const multi = requireChart(charts, EXPECTED_TITLES.multiDistribution);
const family = requireChart(charts, EXPECTED_TITLES.familyDistribution);
const controls = parseMethodologyControls(methodologyHtml);

if (means.categories.length !== 8 || means.series.length !== 2) {
  throw new Error("unexpected mean-by-period chart shape");
}
if (family.categories.length !== 59 || multi.categories.length !== 59) {
  throw new Error("unexpected energy-distribution bin count");
}
if (family.series.length !== 8 || multi.series.length !== 8) {
  throw new Error("unexpected construction-period series count");
}

const buildingTypeSources = [
  {
    buildingType: "FAMILY_HOUSE",
    meanSeries: means.series.find((series) => series.name === "Családi ház"),
    distribution: family,
  },
  {
    buildingType: "MULTI_DWELLING",
    meanSeries: means.series.find(
      (series) => series.name === "Lakás többlakásos épületben",
    ),
    distribution: multi,
  },
];

const benchmarkRows = [];
const distributionRows = [];
for (const source of buildingTypeSources) {
  if (!source.meanSeries) throw new Error(`missing mean series for ${source.buildingType}`);
  for (let periodIndex = 0; periodIndex < means.categories.length; periodIndex += 1) {
    const period = means.categories[periodIndex];
    const distributionSeries = source.distribution.series.find((series) => series.name === period);
    if (!distributionSeries) {
      throw new Error(`missing distribution for ${source.buildingType}/${period}`);
    }
    benchmarkRows.push([
      `BENCH-B02-${source.buildingType}-${String(periodIndex + 1).padStart(2, "0")}`,
      SOURCE_ID,
      2022,
      "EKM_9_2023",
      source.buildingType,
      period,
      source.meanSeries.data[periodIndex],
      sum(distributionSeries.data),
      "MODELLED",
      PUBLICATION_URL,
      retrievedAt,
      publicationSha256,
      "A mean is a KSH random-forest estimate; count is the sum of published 10–590 kWh/m²/year chart bins.",
    ]);
    for (let binIndex = 0; binIndex < source.distribution.categories.length; binIndex += 1) {
      distributionRows.push([
        `DIST-B02-${source.buildingType}-${String(periodIndex + 1).padStart(2, "0")}-${String(binIndex + 1).padStart(2, "0")}`,
        SOURCE_ID,
        2022,
        "EKM_9_2023",
        source.buildingType,
        period,
        Number(source.distribution.categories[binIndex]),
        distributionSeries.data[binIndex],
        "MODELLED",
        PUBLICATION_URL,
        retrievedAt,
        publicationSha256,
      ]);
    }
  }
}

const familyCount = benchmarkRows
  .filter((row) => row[4] === "FAMILY_HOUSE")
  .reduce((total, row) => total + row[7], 0);
const multiCount = benchmarkRows
  .filter((row) => row[4] === "MULTI_DWELLING")
  .reduce((total, row) => total + row[7], 0);
const publishedBinTotal = familyCount + multiCount;
const residual = controls.censusDwellingUniverse - publishedBinTotal;
const distributionCoverage = publishedBinTotal / controls.censusDwellingUniverse;
const linkedCertificateRate = controls.linkedCertificates / controls.censusDwellingUniverse;

const coverageRows = [
  ["COV-B02-CENSUS-UNIVERSE", METHOD_SOURCE_ID, "census_dwelling_universe", controls.censusDwellingUniverse, "dwelling", "OBS", "KSH methodology table 1 total", METHODOLOGY_URL, retrievedAt, methodologySha256],
  ["COV-B02-LINKED-CERTIFICATES", METHOD_SOURCE_ID, "linked_energy_certificates", controls.linkedCertificates, "dwelling", "OBS", "KSH methodology table 1 total", METHODOLOGY_URL, retrievedAt, methodologySha256],
  ["COV-B02-LINK-RATE-PUBLISHED", METHOD_SOURCE_ID, "linked_certificate_rate_published", controls.publishedLinkRatePercent / 100, "ratio", "OBS", "KSH methodology table 1 rounded percentage", METHODOLOGY_URL, retrievedAt, methodologySha256],
  ["COV-B02-LINK-RATE-CALCULATED", METHOD_SOURCE_ID, "linked_certificate_rate_calculated", linkedCertificateRate, "ratio", "DER", "linked_energy_certificates / census_dwelling_universe", METHODOLOGY_URL, retrievedAt, methodologySha256],
  ["COV-B02-FAMILY-PUBLISHED-BINS", SOURCE_ID, "family_house_records_in_published_bins", familyCount, "dwelling", "MODELLED", "sum of Figure 4 published bins", PUBLICATION_URL, retrievedAt, publicationSha256],
  ["COV-B02-MULTI-PUBLISHED-BINS", SOURCE_ID, "multi_dwelling_records_in_published_bins", multiCount, "dwelling", "MODELLED", "sum of Figure 3 published bins", PUBLICATION_URL, retrievedAt, publicationSha256],
  ["COV-B02-ALL-PUBLISHED-BINS", SOURCE_ID, "all_records_in_published_bins", publishedBinTotal, "dwelling", "DER", "family_house_records_in_published_bins + multi_dwelling_records_in_published_bins", PUBLICATION_URL, retrievedAt, publicationSha256],
  ["COV-B02-PUBLISHED-BIN-RESIDUAL", `${SOURCE_ID};${METHOD_SOURCE_ID}`, "published_bin_residual", residual, "dwelling", "DER", "census_dwelling_universe - all_records_in_published_bins", PUBLICATION_URL, retrievedAt, publicationSha256],
  ["COV-B02-PUBLISHED-BIN-COVERAGE", `${SOURCE_ID};${METHOD_SOURCE_ID}`, "published_bin_coverage", distributionCoverage, "ratio", "DER", "all_records_in_published_bins / census_dwelling_universe", PUBLICATION_URL, retrievedAt, publicationSha256],
];

const energyClassRows = [];
for (const series of energyClass.series) {
  const regulation = series.name.startsWith("TNM") ? "TNM_7_2006" : "EKM_9_2023";
  for (let index = 0; index < series.data.length; index += 1) {
    energyClassRows.push([
      `CLASS-B02-${regulation}-${String(index + 1).padStart(2, "0")}`,
      SOURCE_ID,
      2022,
      regulation,
      energyClass.categories[index],
      series.data[index],
      "thousand_dwelling",
      "MODELLED",
      PUBLICATION_URL,
      retrievedAt,
      publicationSha256,
      "Published chart values are rounded to thousand dwellings.",
    ]);
  }
}

await fs.mkdir(outputDir, { recursive: true });
const outputs = {
  benchmarks: path.join(outputDir, "ksh_energy_archetype_benchmarks_2022.csv"),
  distribution: path.join(outputDir, "ksh_energy_distribution_2022.csv"),
  energyClasses: path.join(outputDir, "ksh_energy_class_distribution_2022.csv"),
  coverage: path.join(outputDir, "ksh_energy_coverage_2022.csv"),
  manifest: path.join(outputDir, "ksh_energy_extract_manifest.json"),
};

await fs.writeFile(
  outputs.benchmarks,
  toCsv(
    ["benchmark_id", "source_id", "reference_year", "regulation", "building_type", "construction_period", "mean_primary_energy_kwh_m2_year", "published_bin_dwelling_count", "evidence_status", "source_url", "retrieved_at", "source_html_sha256", "notes"],
    benchmarkRows,
  ),
  "utf8",
);
await fs.writeFile(
  outputs.distribution,
  toCsv(
    ["distribution_id", "source_id", "reference_year", "regulation", "building_type", "construction_period", "published_energy_bin_kwh_m2_year", "dwelling_count", "evidence_status", "source_url", "retrieved_at", "source_html_sha256"],
    distributionRows,
  ),
  "utf8",
);
await fs.writeFile(
  outputs.energyClasses,
  toCsv(
    ["class_id", "source_id", "reference_year", "regulation", "published_class_label", "dwelling_count_thousand", "unit", "evidence_status", "source_url", "retrieved_at", "source_html_sha256", "notes"],
    energyClassRows,
  ),
  "utf8",
);
await fs.writeFile(
  outputs.coverage,
  toCsv(
    ["coverage_id", "source_ids", "metric", "value", "unit", "evidence_status", "calculation", "source_url", "retrieved_at", "source_html_sha256"],
    coverageRows,
  ),
  "utf8",
);

const manifest = {
  schema_version: "1.0.0",
  module_id: "B02",
  source_ids: [SOURCE_ID, METHOD_SOURCE_ID],
  retrieved_at: retrievedAt,
  publication: { url: PUBLICATION_URL, sha256: publicationSha256 },
  methodology: { url: METHODOLOGY_URL, sha256: methodologySha256 },
  outputs: Object.fromEntries(
    Object.entries(outputs)
      .filter(([name]) => name !== "manifest")
      .map(([name, outputPath]) => [name, outputPath.replaceAll("\\", "/")]),
  ),
  controls: {
    chart_count: charts.length,
    benchmark_rows: benchmarkRows.length,
    distribution_rows: distributionRows.length,
    energy_class_rows: energyClassRows.length,
    census_dwelling_universe: controls.censusDwellingUniverse,
    linked_energy_certificates: controls.linkedCertificates,
    family_house_records_in_published_bins: familyCount,
    multi_dwelling_records_in_published_bins: multiCount,
    all_records_in_published_bins: publishedBinTotal,
    published_bin_residual: residual,
    published_bin_coverage: distributionCoverage,
  },
};
await fs.writeFile(outputs.manifest, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");

console.log(
  `VALID: charts=${charts.length} benchmarks=${benchmarkRows.length} ` +
    `distribution=${distributionRows.length} classes=${energyClassRows.length} ` +
    `coverage=${distributionCoverage.toFixed(6)} residual=${residual}`,
);
