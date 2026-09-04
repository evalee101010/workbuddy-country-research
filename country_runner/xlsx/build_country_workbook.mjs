import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";


async function loadArtifactTool() {
  try {
    return await import("@oai/artifact-tool");
  } catch (initialError) {
    const modulesRoot = process.env.COUNTRY_RUNNER_NODE_MODULES;
    if (!modulesRoot) throw initialError;
    const require = createRequire(import.meta.url);
    const resolved = require.resolve("@oai/artifact-tool", { paths: [modulesRoot] });
    return await import(pathToFileURL(resolved).href);
  }
}


function columnName(index) {
  let number = index + 1;
  let output = "";
  while (number > 0) {
    const remainder = (number - 1) % 26;
    output = String.fromCharCode(65 + remainder) + output;
    number = Math.floor((number - 1) / 26);
  }
  return output;
}


function safeValue(value) {
  if (typeof value === "string" && value.startsWith("=")) return `'${value}`;
  return value ?? "";
}


function matrixFor(table) {
  const headers = table.headers || ["No data"];
  const rows = (table.rows || []).map((row) => headers.map((_, index) => safeValue(row[index])));
  return [headers.map(safeValue), ...rows];
}


function styleDataSheet(sheet, table, sheetName) {
  const matrix = matrixFor(table);
  const rowCount = matrix.length;
  const columnCount = matrix[0].length;
  const lastColumn = columnName(columnCount - 1);
  sheet.getRange(`A1:${lastColumn}${rowCount}`).values = matrix;
  sheet.getRange(`A1:${lastColumn}1`).format = {
    fill: "#164E63",
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
    verticalAlignment: "center",
  };
  sheet.getRange(`A1:${lastColumn}${rowCount}`).format.font = { name: "Aptos", size: 10 };
  sheet.getRange(`A2:${lastColumn}${rowCount}`).format.wrapText = true;
  sheet.getRange(`A1:${lastColumn}${rowCount}`).format.verticalAlignment = "top";
  sheet.freezePanes.freezeRows(1);
  sheet.showGridLines = false;

  for (let index = 0; index < columnCount; index += 1) {
    const header = String(matrix[0][index] || "").toLowerCase();
    const column = columnName(index);
    let width = 18;
    if (header.includes("original_text") || header.includes("translation") || header.includes("context") || header.includes("note") || header.includes("reason")) width = 42;
    else if (header.includes("url")) width = 34;
    else if (header.includes("id")) width = 23;
    else if (header === "code") width = 32;
    else if (header === "message") width = 48;
    else if (header.includes("date") || header.includes("status") || header.includes("confidence")) width = 16;
    sheet.getRange(`${column}1:${column}${rowCount}`).format.columnWidth = width;
    if (rowCount > 1 && (header.includes("date") || header.endsWith("_at"))) {
      sheet.getRange(`${column}2:${column}${rowCount}`).format.numberFormat = "yyyy-mm-dd hh:mm";
    }
  }
  sheet.getRange(`A1:${lastColumn}1`).format.rowHeight = 30;
  const rowHeight = ["Source Plan", "Warnings"].includes(sheetName)
    ? 66
    : (["Raw Discovery", "A", "B", "C", "Citation Index"].includes(sheetName) ? 52 : 36);
  if (rowCount > 1) sheet.getRange(`A2:${lastColumn}${rowCount}`).format.rowHeight = rowHeight;
}


const [inputPath, outputPath, previewDir, inspectionPath] = process.argv.slice(2);
if (!inputPath || !outputPath || !previewDir || !inspectionPath) {
  throw new Error("Usage: build_country_workbook.mjs INPUT_JSON OUTPUT_XLSX PREVIEW_DIR INSPECTION_JSON");
}

const payload = JSON.parse(await fs.readFile(inputPath, "utf8"));
const artifact = await loadArtifactTool();
const { Workbook, SpreadsheetFile } = artifact;
const workbook = Workbook.create();
const sheetNames = [
  "Summary", "Source Plan", "Raw Discovery", "A", "B", "C",
  "Coverage", "Audit", "Warnings", "Citation Index",
];
for (const name of sheetNames) workbook.worksheets.add(name);

for (const name of sheetNames.slice(1)) {
  const sheet = workbook.worksheets.getItem(name);
  const table = payload.tables[name] || { headers: ["No data"], rows: [] };
  styleDataSheet(sheet, table, name);
}

const summary = workbook.worksheets.getItem("Summary");
summary.showGridLines = false;
summary.getRange("A1").values = [["Country Public Demand Signal Pack"]];
summary.getRange("A1:D1").format = {
  fill: "#0F3D4C",
  font: { bold: true, color: "#FFFFFF", size: 18 },
  rowHeight: 32,
  verticalAlignment: "center",
};
summary.getRange("A3:B11").values = [
  ["Country", `${payload.summary.country_iso2} / ${payload.summary.country_iso3}`],
  ["Run ID", payload.summary.run_id],
  ["Validation state", payload.summary.validation_state],
  ["Research window", `${payload.summary.research_window.start || ""} — ${payload.summary.research_window.end || ""}`],
  ["Researcher", payload.summary.researcher],
  ["Reviewer", payload.summary.reviewer],
  ["Gate A approved by", payload.summary.source_plan_approved_by],
  ["Gate B approved by", payload.summary.evidence_audit_approved_by],
  ["Interpretation", "Public signals only; not market share or population demand."],
];
summary.getRange("A3:A11").format = { fill: "#DDF3F0", font: { bold: true, color: "#164E63" } };
summary.getRange("A3:B11").format.wrapText = true;
summary.getRange("A3:B11").format.borders = { preset: "outside", style: "thin", color: "#A7C7C4" };
summary.getRange("A13:B13").values = [["Evidence stream", "Included rows"]];
summary.getRange("A13:B13").format = { fill: "#164E63", font: { bold: true, color: "#FFFFFF" } };
summary.getRange("A14:A17").values = [["A"], ["B"], ["C"], ["Warnings"]];
summary.getRange("B14").formulas = [["=MAX(COUNTA('A'!A1:A1000)-1,0)"]];
summary.getRange("B15").formulas = [["=MAX(COUNTA('B'!A1:A1000)-1,0)"]];
summary.getRange("B16").formulas = [["=MAX(COUNTA('C'!A1:A1000)-1,0)"]];
summary.getRange("B17").formulas = [["=MAX(COUNTA('Warnings'!A1:A1000)-1,0)"]];
summary.getRange("A13:B17").format.borders = { preset: "outside", style: "thin", color: "#A7C7C4" };
summary.getRange("A1:D17").format.font = { name: "Aptos" };
summary.getRange("A3:B10").format.rowHeight = 26;
summary.getRange("A11:B11").format.rowHeight = 44;
summary.getRange("A1:A17").format.columnWidth = 24;
summary.getRange("B1:B17").format.columnWidth = 54;
summary.freezePanes.freezeRows(1);

await fs.mkdir(previewDir, { recursive: true });
const inspections = {};
for (const name of sheetNames) {
  const table = name === "Summary" ? { headers: ["", ""], rows: Array(16).fill(["", ""]) } : payload.tables[name];
  const rowCount = name === "Summary" ? 17 : Math.min((table?.rows?.length || 0) + 1, 12);
  const columnCount = Math.min(table?.headers?.length || 2, 12);
  const range = `A1:${columnName(Math.max(columnCount - 1, 1))}${Math.max(rowCount, 3)}`;
  const inspection = await workbook.inspect({
    kind: "region",
    sheetId: name,
    range,
    maxChars: 3500,
  });
  inspections[name] = inspection.ndjson;
  const preview = await workbook.render({ sheetName: name, range, scale: 1, format: "png" });
  const filename = `${String(sheetNames.indexOf(name) + 1).padStart(2, "0")}-${name.replaceAll(" ", "-")}.png`;
  await fs.writeFile(path.join(previewDir, filename), new Uint8Array(await preview.arrayBuffer()));
}
const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
inspections.formulaErrors = formulaErrors.ndjson;
const implementationNotices = await workbook.inspect({
  kind: "match",
  searchTerm: "not implemented",
  options: { matchCase: false, maxResults: 100 },
  summary: "unsupported feature notice scan",
});
inspections.implementationNotices = implementationNotices.ndjson;
await fs.writeFile(inspectionPath, JSON.stringify(inspections, null, 2), "utf8");

const exported = await SpreadsheetFile.exportXlsx(workbook);
await exported.save(outputPath);
