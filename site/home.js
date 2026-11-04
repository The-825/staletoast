"use strict";
// Shows only the latest chart edition date, read from data/charts.json.
// No catalog counts are derived here. If the file cannot be read, the page keeps its static text.
function latestEditionText(chartData) {
  const date = chartData && chartData.latest && chartData.latest.edition_date;
  return /^\d{4}-\d{2}-\d{2}$/.test(String(date))
    ? `Latest edition: ${date}. The date marks an editorial reevaluation, not the freshness of each source.`
    : "";
}
async function showEdition() {
  const target = document.querySelector("#edition-date");
  const response = await fetch("data/charts.json");
  if (!response.ok) throw new Error("Chart data unavailable");
  const text = latestEditionText(await response.json());
  if (text) target.textContent = text;
}
if (typeof document !== "undefined" && document.querySelector("#edition-date")) showEdition().catch(() => {});
