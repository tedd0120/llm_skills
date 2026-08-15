#!/usr/bin/env node

import assert from "node:assert/strict";
import { zstdDecompressSync } from "node:zlib";

function parseObject(value, label) {
  if (typeof value !== "string") return value;
  try {
    return JSON.parse(value);
  } catch (error) {
    throw new Error(`${label} is not valid JSON: ${error.message}`);
  }
}

export function decodeResult(detail) {
  const body = parseObject(detail?.body ?? detail, "response body");
  if (!body || typeof body !== "object" || !body.data) {
    throw new Error("Expected an OpenCLI getResult detail response with body.data");
  }
  if (body.flag && body.flag !== "S") {
    throw new Error(`Query API failed: flag=${body.flag}, msg=${body.msg ?? ""}`);
  }

  const data = body.data;
  if (data.success === false) {
    throw new Error(
      `Query failed: jobId=${data.jobId ?? "unknown"}, status=${data.status ?? "unknown"}, ` +
        `message=${data.executeException ?? data.errorMsg ?? body.msg ?? "unknown"}`,
    );
  }

  let rows = data.resultData;
  if (!Array.isArray(rows) && data.compressedData) {
    const compressed = Buffer.from(data.compressedData, "base64");
    const json = zstdDecompressSync(compressed).toString("utf8");
    rows = parseObject(json, "decompressed result");
  }
  if (rows == null) rows = [];
  if (!Array.isArray(rows)) {
    throw new Error("Decoded result is not a row array");
  }

  let other = {};
  if (data.other) other = parseObject(data.other, "body.data.other");

  return {
    jobId: data.jobId ?? null,
    status: data.status ?? null,
    success: data.success ?? null,
    sqlType: data.sqlType ?? null,
    rawSql: other.rawSql ?? null,
    columns: Array.isArray(data.columnNameList) ? data.columnNameList : [],
    rows,
    totalCount: data.resultTotalCount ?? data.totalCount ?? rows.length,
    costTimeMs: data.costTimeMill ?? null,
    displayCostTime: data.displayCostTime ?? null,
    dataSource: data.dataSourceType ?? null,
    dataCenter: data.dataCenterType ?? null,
    canDownload: data.canDownload ?? false,
  };
}

function selfTest() {
  const decoded = decodeResult({
    body: {
      flag: "S",
      data: {
        jobId: "smoke",
        status: 2,
        success: true,
        columnNameList: ["codex_smoke_test"],
        compressedData: "KLUv/SAHOQAAW1siMSJdXQ==",
        totalCount: 1,
        other: '{"rawSql":"select 1 as codex_smoke_test"}',
      },
    },
  });
  assert.deepEqual(decoded.columns, ["codex_smoke_test"]);
  assert.deepEqual(decoded.rows, [["1"]]);
  assert.equal(decoded.rawSql, "select 1 as codex_smoke_test");
  process.stdout.write("decode-result self-test passed\n");
}

async function main() {
  if (process.argv.includes("--self-test")) {
    selfTest();
    return;
  }

  let input = "";
  for await (const chunk of process.stdin) input += chunk;
  if (!input.trim()) {
    throw new Error("Pass an OpenCLI network --detail JSON response on stdin");
  }
  const decoded = decodeResult(parseObject(input, "stdin"));
  process.stdout.write(`${JSON.stringify(decoded, null, 2)}\n`);
}

main().catch((error) => {
  process.stderr.write(`decode-result: ${error.message}\n`);
  process.exitCode = 1;
});
