// Builds an animated "rocket over the contribution grid" SVG.
// Zero dependencies (node >=18). Inline SVG attributes only — GitHub's sanitiser strips
// <style>, which would flatten every colour.
//
// The grid is SYNTHETIC by design: a dense, good-looking activity pattern rather than the
// real (sparse) calendar, so the header always reads as an active year. Set MODE="real"
// with a GH_TOKEN to fetch the actual contribution calendar instead.
import { writeFile, mkdir } from "node:fs/promises";
import { dirname } from "node:path";

const LOGIN = process.env.LOGIN || "RFNOACH";
const TOKEN = process.env.GH_TOKEN;
const MODE = process.env.MODE || "synthetic";
const OUT = process.env.OUTPUT_PATH || "dist/github-rocket.svg";
const WEEKS = 53;

// GitHub dark contribution palette
const LEVELS = {
  NONE: "#161b22",
  FIRST_QUARTILE: "#0e4429",
  SECOND_QUARTILE: "#006d32",
  THIRD_QUARTILE: "#26a641",
  FOURTH_QUARTILE: "#39d353",
};

const CELL = 11, GAP = 3, PITCH = CELL + GAP;
const PAD_X = 22, TOP = 54, BOTTOM = 34;
const FLIGHT = 14; // seconds per lap

async function fetchCalendar() {
  const query = `query($login:String!){
    user(login:$login){ contributionsCollection{ contributionCalendar{
      totalContributions
      weeks{ contributionDays{ date contributionCount contributionLevel } }
    }}}}`;

  const res = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      "Content-Type": "application/json",
      "User-Agent": "github-rocket-heatmap",
    },
    body: JSON.stringify({ query, variables: { login: LOGIN } }),
  });

  if (!res.ok) throw new Error(`GitHub API ${res.status}: ${await res.text()}`);
  const json = await res.json();
  if (json.errors) throw new Error(JSON.stringify(json.errors));
  return json.data.user.contributionsCollection.contributionCalendar;
}

const LEVEL_NAMES = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"];

// Deterministic-per-day pseudo random so the pattern is stable within a run.
function rng(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

// A dense, believable year: weekday-heavy, a couple of quiet stretches, occasional
// hot streaks. Weekends lighter. Almost every day has at least something.
function syntheticCalendar() {
  const end = new Date();
  end.setUTCHours(0, 0, 0, 0);
  const start = new Date(end);
  start.setUTCDate(start.getUTCDate() - (WEEKS * 7 - 1));
  start.setUTCDate(start.getUTCDate() - start.getUTCDay()); // align to Sunday

  const rand = rng(0xC0FFEE);
  const weeks = [];
  let total = 0;

  for (let w = 0; w < WEEKS; w++) {
    const season = 0.8 + 0.35 * Math.sin((w / WEEKS) * Math.PI * 2 + 1); // gentle ebb/flow
    const lull = w % 19 === 0 ? 0.6 : 1; // rare, mild quiet week
    const days = [];
    for (let d = 0; d < 7; d++) {
      const date = new Date(start);
      date.setUTCDate(start.getUTCDate() + w * 7 + d);
      if (date > end) continue;

      const weekend = d === 0 || d === 6 ? 0.7 : 1;
      const streak = rand() < 0.14 ? 1.7 : 1; // random hot days
      let score = season * lull * weekend * streak * (0.6 + rand() * 0.9);

      let level = 1;                     // almost every day shows activity
      if (score > 0.22) level = 1;
      if (score > 0.72) level = 2;
      if (score > 1.15) level = 3;
      if (score > 1.6) level = 4;
      if (score < 0.14) level = 0;       // only the quietest days stay blank

      const count = level === 0 ? (rand() < 0.4 ? 0 : 1) : Math.round(level * 3 + rand() * 4);
      total += count;
      days.push({ date: date.toISOString().slice(0, 10), contributionCount: count, contributionLevel: LEVEL_NAMES[level] });
    }
    weeks.push({ contributionDays: days });
  }
  return { totalContributions: total, weeks };
}

function build(cal) {
  const weeks = cal.weeks;
  const W = PAD_X * 2 + weeks.length * PITCH - GAP;
  const gridH = 7 * PITCH - GAP;
  const H = TOP + gridH + BOTTOM;

  const p = [];
  p.push(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" ` +
      `font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" role="img" ` +
      `aria-label="${cal.totalContributions} contributions in the last year">`
  );

  // card
  p.push(`<rect width="${W}" height="${H}" rx="12" fill="#0d1117"/>`);
  p.push(`<rect x="0.5" y="0.5" width="${W - 1}" height="${H - 1}" rx="12" fill="none" stroke="#30363d"/>`);
  p.push(
    `<text x="${PAD_X}" y="30" fill="#c9d1d9" font-size="13">` +
      `${cal.totalContributions} contributions in the last year</text>`
  );

  // cells
  const hot = [];
  weeks.forEach((week, wi) => {
    week.contributionDays.forEach((day) => {
      const di = new Date(day.date + "T00:00:00Z").getUTCDay();
      const x = PAD_X + wi * PITCH;
      const y = TOP + di * PITCH;
      p.push(
        `<rect x="${x}" y="${y}" width="${CELL}" height="${CELL}" rx="2" ` +
          `fill="${LEVELS[day.contributionLevel]}"/>`
      );
      if (day.contributionLevel === "FOURTH_QUARTILE" || day.contributionLevel === "THIRD_QUARTILE") {
        hot.push([x + CELL / 2, y + CELL / 2]);
      }
    });
  });

  // pulsing rings on the busiest days
  hot.slice(0, 14).forEach(([cx, cy], i) => {
    const begin = ((i * 0.9) % FLIGHT).toFixed(2);
    p.push(
      `<circle cx="${cx}" cy="${cy}" r="5" fill="none" stroke="#39d353" stroke-width="1.2" opacity="0">` +
        `<animate attributeName="r" values="4;11" begin="${begin}s" dur="2.2s" repeatCount="indefinite"/>` +
        `<animate attributeName="opacity" values="0.9;0" begin="${begin}s" dur="2.2s" repeatCount="indefinite"/>` +
        `</circle>`
    );
  });

  // flight path: a gentle wave across the middle of the grid
  const midY = TOP + gridH / 2;
  const path =
    `M ${-30} ${midY} ` +
    `C ${W * 0.25} ${midY - gridH * 0.55}, ${W * 0.4} ${midY + gridH * 0.5}, ${W * 0.55} ${midY} ` +
    `S ${W * 0.85} ${midY - gridH * 0.45}, ${W + 40} ${midY}`;
  p.push(`<path id="flight" d="${path}" fill="none" stroke="none"/>`);

  // thrust trail: dots riding the same path, staggered and fading
  for (let i = 1; i <= 7; i++) {
    const delay = (i * 0.075).toFixed(3);
    p.push(
      `<circle r="${(3.2 - i * 0.3).toFixed(1)}" fill="#58a6ff" opacity="${(0.5 - i * 0.06).toFixed(2)}">` +
        `<animateMotion dur="${FLIGHT}s" begin="-${delay}s" repeatCount="indefinite" rotate="auto">` +
        `<mpath href="#flight"/></animateMotion></circle>`
    );
  }

  // rocket
  p.push(
    `<g><animateMotion dur="${FLIGHT}s" repeatCount="indefinite" rotate="auto">` +
      `<mpath href="#flight"/></animateMotion>` +
      `<g transform="rotate(90)">` +
      `<path d="M0,-11 C4.2,-5.4 5.6,1.2 5.6,5.4 L-5.6,5.4 C-5.6,1.2 -4.2,-5.4 0,-11 Z" fill="#e6edf3"/>` +
      `<path d="M-5.6,5.4 L-9.4,10 L-4,8.4 Z" fill="#58a6ff"/>` +
      `<path d="M5.6,5.4 L9.4,10 L4,8.4 Z" fill="#58a6ff"/>` +
      `<circle cy="-3.4" r="2.1" fill="#0d1117"/>` +
      `<path d="M-2.6,8.4 L0,16 L2.6,8.4 Z" fill="#f0883e" opacity="0.95">` +
      `<animate attributeName="opacity" values="0.95;0.35;0.95" dur="0.28s" repeatCount="indefinite"/>` +
      `<animateTransform attributeName="transform" type="scale" values="1 1;1 0.55;1 1" ` +
      `dur="0.28s" repeatCount="indefinite"/></path>` +
      `</g></g>`
  );

  // legend
  const ly = TOP + gridH + 20;
  p.push(`<text x="${PAD_X}" y="${ly}" fill="#7d8590" font-size="10.5">Less</text>`);
  ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"].forEach((k, i) => {
    p.push(
      `<rect x="${PAD_X + 32 + i * 14}" y="${ly - 8}" width="10" height="10" rx="2" fill="${LEVELS[k]}"/>`
    );
  });
  p.push(`<text x="${PAD_X + 108}" y="${ly}" fill="#7d8590" font-size="10.5">More</text>`);
  p.push(`<text x="${W - PAD_X}" y="${ly}" fill="#7d8590" font-size="10.5" text-anchor="end">@${LOGIN}</text>`);

  p.push("</svg>");
  return p.join("");
}

const cal = MODE === "real" ? await fetchCalendar() : syntheticCalendar();
const svg = build(cal);
await mkdir(dirname(OUT), { recursive: true });
await writeFile(OUT, svg);
console.log(`${OUT} written (${svg.length} bytes)`);
