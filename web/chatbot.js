/*
 * GFC Financial Chatbot: browser version.
 * A line-for-line port of chatbot/financial_chatbot.py (FinancialChatbot), so the
 * web demo behaves exactly like the Python chatbot. The keyword dictionaries,
 * context notes and data are exported from the Python code by
 * scripts/build_web_demo.py, and scripts/parity_test.py checks that both
 * versions give identical answers.
 */
(function (root) {
  "use strict";

  function escapeRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }

  function contains(text, phrase) {
    phrase = phrase.trim();
    return new RegExp("(?<![a-z0-9])" + escapeRe(phrase) + "(?![a-z0-9])").test(text);
  }

  function fixed(x, d) { return Number(x).toFixed(d); }
  function signed(x, d) { const v = Number(x).toFixed(d); return (Number(x) >= 0 && !v.startsWith("-") ? "+" : "") + v; }
  function commas(x, d) {
    const [i, f] = Math.abs(Number(x)).toFixed(d).split(".");
    const s = i.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return (Number(x) < 0 ? "-" : "") + s + (f ? "." + f : "");
  }
  function formatMoney(millions) {
    if (Math.abs(millions) >= 1000) return "$" + commas(millions / 1000, 1) + "bn";
    return "$" + commas(millions, 0) + "m";
  }
  function formatValue(v, kind) { return kind === "money" ? formatMoney(v) : fixed(v, 1) + "%"; }
  function describeChange(pct) {
    if (Math.abs(pct) < 0.05) return "was unchanged";
    return (pct > 0 ? "rose" : "fell") + " " + fixed(Math.abs(pct), 1) + "%";
  }
  function capitalize(s) { return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase(); }
  function title(s) { return s.replace(/\b\w/g, c => c.toUpperCase()); }
  function bankersRound(x) {
    const f = Math.floor(x), diff = x - f;
    if (diff > 0.5) return f + 1;
    if (diff < 0.5) return f;
    return f % 2 === 0 ? f : f + 1;
  }
  function cagr(first, last, periods) { return (Math.pow(last / first, 1 / periods) - 1) * 100; }

  class FinancialChatbot {
    constructor(K, rows, suggestions = true) {
      this.K = K;
      this.suggestions = suggestions;
      this.df = rows.slice().sort((a, b) =>
        a["Company"] < b["Company"] ? -1 : a["Company"] > b["Company"] ? 1 : a["Fiscal Year"] - b["Fiscal Year"]);
      this.companies = [...new Set(this.df.map(r => r["Company"]))].sort();
      this.years = [...new Set(this.df.map(r => r["Fiscal Year"]))].sort((a, b) => a - b);
      this.latestYear = this.years[this.years.length - 1];
      this.memory = { companies: [], metric: null, year: null, intent: null };
    }

    // ---------------- understanding the question ----------------
    findCompanies(text) {
      let found = Object.entries(this.K.COMPANY_ALIASES)
        .filter(([name, aliases]) => this.companies.includes(name) && aliases.some(a => contains(text, a)))
        .map(([name]) => name);
      if (!found.length && ["all three", "all companies", "each company", "every company"].some(p => contains(text, p)))
        found = this.companies.slice();
      return found;
    }
    findOutOfScope(text) {
      for (const name of this.K.OUT_OF_SCOPE_COMPANIES)
        if (contains(text, name)) return (name === "ibm" || name === "byd") ? name.toUpperCase() : title(name);
      return null;
    }
    findMetric(text) {
      let best = null;
      for (const [key, m] of Object.entries(this.K.METRICS))
        for (const k of m.keywords)
          if (contains(text, k)) {
            const cand = [k.length, key];
            if (!best || cand[0] > best[0] || (cand[0] === best[0] && cand[1] > best[1])) best = cand;
          }
      return best ? best[1] : null;
    }
    findYear(text) {
      const m = text.match(/\b(?:fy\s?)?(20\d{2})\b/) || text.match(/\bfy\s?(\d{2})\b/);
      if (m) {
        let year = parseInt(m[1], 10);
        if (year < 100) year += 2000;
        return this.years.includes(year) ? year : "out_of_range:" + year;
      }
      if (["latest", "most recent", "this year", "current", "recent", "now", "last year", "past year",
           "last fiscal year"].some(p => contains(text, p))) return this.latestYear;
      if (["previous year", "prior year", "year before"].some(p => contains(text, p))) return this.latestYear - 1;
      return null;
    }
    findIntent(text) {
      for (const intent of ["advice", "help", "goodbye", "thanks", "chart", "compare", "trend", "change", "summary", "greeting"])
        if (this.K.INTENT_KEYWORDS[intent].some(k => k.trim() === k ? contains(text, k) : (" " + text + " ").includes(k)))
          return intent;
      return null;
    }

    // ---------------- data ----------------
    row(company, year) { return this.df.find(r => r["Company"] === company && r["Fiscal Year"] === year); }
    series(company, column) { return this.df.filter(r => r["Company"] === company).map(r => r[column]); }
    noteKey(company, metric, year) { return company + "|" + metric + "|" + (year === null ? "None" : year); }
    note(company, metric, year) {
      const n = this.K.CONTEXT_NOTES[this.noteKey(company, metric, year)] || this.K.CONTEXT_NOTES[this.noteKey(company, metric, null)];
      return n ? "\n  Context: " + n : "";
    }

    // ---------------- answers ----------------
    answerValue(company, metric, year) {
      const m = this.K.METRICS[metric], r = this.row(company, year);
      const verb = m.label.startsWith("total") && m.label.endsWith("s") ? "were" : "was";
      let t = `${company}'s ${m.label} in FY${year} ${verb} ${formatValue(r[m.column], m.kind)}`;
      if (m.growth && r[m.growth] !== null && r[m.growth] !== undefined)
        t += `, which ${describeChange(r[m.growth])} on FY${year - 1}`;
      t += ".";
      if (m.meaning) t += ` This measures ${m.meaning}.`;
      return t + this.note(company, metric, year);
    }
    answerChange(company, metric, year) {
      const m = this.K.METRICS[metric];
      if (year === this.years[0])
        return `FY${year} is the first year in my data, so I can't calculate a change for it. ` +
               `Try asking about FY${year + 1} or FY${this.latestYear}.`;
      const nw = this.row(company, year)[m.column], old = this.row(company, year - 1)[m.column];
      let t;
      if (m.kind === "percent") {
        const diff = nw - old;
        t = `${company}'s ${m.label} ${diff > 0 ? "rose" : "fell"} from ${fixed(old, 1)}% in FY${year - 1} ` +
            `to ${fixed(nw, 1)}% in FY${year}, a change of ${signed(diff, 1)} percentage points.`;
      } else {
        const pct = (nw / old - 1) * 100;
        t = `${company}'s ${m.label} ${describeChange(pct)} in FY${year}, from ${formatMoney(old)} to ${formatMoney(nw)}.`;
      }
      return t + this.note(company, metric, year);
    }
    answerTrend(company, metric) {
      const m = this.K.METRICS[metric];
      const data = this.df.filter(r => r["Company"] === company);
      const path = data.map(r => `FY${r["Fiscal Year"]} ${formatValue(r[m.column], m.kind)}`).join(" → ");
      const first = data[0][m.column], last = data[data.length - 1][m.column];
      const summary = m.kind === "money"
        ? `That is an average change of ${signed(cagr(first, last, data.length - 1), 1)}% a year.`
        : `Overall, a change of ${signed(last - first, 1)} percentage points.`;
      let notes = "";
      for (const r of data)
        if (this.K.CONTEXT_NOTES[this.noteKey(company, metric, r["Fiscal Year"])] !== undefined) {
          notes = this.note(company, metric, r["Fiscal Year"]); break;
        }
      return `${company}'s ${m.label}: ${path}. ${summary}` + (notes || this.note(company, metric, null));
    }
    answerGrowthRanking(companies, metric, text) {
      const m = this.K.METRICS[metric];
      companies = companies.length >= 2 ? companies : this.companies.slice();
      const periods = this.years.length - 1;
      const rows = companies.map(c => {
        const s = this.series(c, m.column);
        return [c, cagr(s[0], s[s.length - 1], periods), this.row(c, this.latestYear)[m.growth]];
      });
      const slowest = ["slowest", "least", "lowest", "worst"].some(w => contains(text, w));
      rows.sort((a, b) => slowest ? a[1] - b[1] : b[1] - a[1]);
      const lines = [`Average annual growth in ${m.label}, FY${this.years[0]} to FY${this.latestYear} ` +
                     `(${slowest ? "slowest" : "fastest"} first):`];
      rows.forEach(([c, g, l], i) => lines.push(`  ${i + 1}. ${c}: ${signed(g, 1)}% a year (FY${this.latestYear}: ${signed(l, 1)}%)`));
      if (slowest && rows[0][1] < 0) lines.push(`${rows[0][0]} performed weakest: its ${m.label} shrank over the period.`);
      else lines.push(`${rows[0][0]} grew ${slowest ? "slowest" : "fastest"}.`);
      return lines.join("\n");
    }
    answerCompare(companies, metric, year, text) {
      const m = this.K.METRICS[metric];
      companies = companies.length >= 2 ? companies : this.companies.slice();
      const data = this.df.filter(r => r["Fiscal Year"] === year && companies.includes(r["Company"]));
      const wantsLow = ["lowest", "smallest", "least", "worst"].some(w => contains(text, w));
      const ascending = m.higher_is_better ? wantsLow : !["highest", "most", "largest", "biggest"].some(w => contains(text, w));
      const ranked = data.slice().sort((a, b) => ascending ? a[m.column] - b[m.column] : b[m.column] - a[m.column]);
      const lines = ranked.map((r, i) => `  ${i + 1}. ${r["Company"]}: ${formatValue(r[m.column], m.kind)}`);
      const lead = ranked[0]["Company"];
      const header = `${capitalize(m.label)} in FY${year} (${ascending ? "lowest first" : "highest first"}):`;
      let footer = `${lead} has the ${ascending ? "lowest" : "highest"} ${m.label}.`;
      if (m.meaning) footer += ` (${capitalize(m.label)} measures ${m.meaning}.)`;
      else if (!m.higher_is_better) footer += ` For ${m.label}, lower generally means a stronger position.`;
      return [header, ...lines, footer].join("\n");
    }
    answerSummary(company) {
      const L = this.row(company, this.latestYear), F = this.row(company, this.years[0]);
      const rc = cagr(F["Total Revenue"], L["Total Revenue"], this.years.length - 1);
      return [
        `${company}: financial health summary (FY${this.years[0]} to FY${this.latestYear})`,
        `  Verdict: ${this.K.HEALTH_VERDICTS[company] || "See the figures below."}`,
        `  Revenue: ${formatMoney(L["Total Revenue"])} in FY${this.latestYear} (average change ${signed(rc, 1)}% a year).`,
        `  Net income: ${formatMoney(L["Net Income"])}, a net margin of ${fixed(L["Net Margin (%)"], 1)}%.`,
        `  Operating cash flow: ${formatMoney(L["Cash Flow from Operating Activities"])} (${fixed(L["OCF to Net Income (x)"], 1)}x net income).`,
        `  Leverage: liabilities fund ${fixed(L["Liabilities to Assets (%)"], 1)}% of assets.`,
      ].join("\n");
    }
    answerChart(companies, metric) {
      const m = this.K.METRICS[metric];
      companies = companies.length ? companies : this.companies.slice();
      const data = this.df.filter(r => companies.includes(r["Company"]));
      const peak = Math.max(...data.map(r => Math.abs(r[m.column])));
      const width = 30;
      const lines = [`${capitalize(m.label)} by fiscal year (each block is about ${formatValue(peak / width, m.kind)}):`];
      for (const c of companies) {
        lines.push(`  ${c}`);
        for (const r of data.filter(r => r["Company"] === c)) {
          const v = r[m.column];
          lines.push(`    FY${r["Fiscal Year"]} ${"█".repeat(Math.max(1, bankersRound(Math.abs(v) / peak * width)))} ${formatValue(v, m.kind)}`);
        }
      }
      const dirs = companies.map(c => {
        const s = data.filter(r => r["Company"] === c).map(r => r[m.column]);
        return `${c} ${s[s.length - 1] > s[0] ? "up" : "down"}`;
      });
      lines.push(`Reading the chart: longer bars mean higher values. Over three years: ${dirs.join(", ")}.`);
      if (this.K.CHART_FILES[metric]) lines.push(`A full line chart of this is saved in the project at ${this.K.CHART_FILES[metric]}.`);
      return lines.join("\n");
    }
    suggest(intent, companies, metric) {
      const company = companies.length ? companies[0] : "Microsoft";
      const other = this.companies.find(c => c !== company);
      const label = metric ? this.K.METRICS[metric].label : "net income";
      const ideas = {
        value: [`How has ${company}'s ${label} changed?`, `Which company has the highest ${label}?`],
        change: [`Show ${company}'s ${label} trend`, `What about ${other}?`],
        trend: [`Show a chart of ${label}`, `How healthy is ${company}?`],
        compare: [`How healthy is ${company}?`, `Show a chart of ${label}`],
        summary: [`Show ${company}'s net income trend`, "Which company has the highest net margin?"],
        chart: [`Which company has the highest ${label}?`, `How healthy is ${company}?`],
      }[intent];
      return ideas ? `\n  You could also ask: "${ideas[0]}" or "${ideas[1]}"` : "";
    }
    help() {
      return "I can answer questions about Microsoft, Tesla and Apple, using their 10-K filings " +
        `for FY${this.years[0]} to FY${this.latestYear}.\n` +
        "  Metrics: revenue, net income, total assets, total liabilities, operating cash flow, " +
        "net margin, leverage and shareholders' equity.\n" +
        "  Try asking:\n" +
        "  - What was Apple's revenue in 2025?\n" +
        "  - How has Tesla's net income changed over the last year?\n" +
        "  - Show Microsoft's operating cash flow trend\n" +
        "  - Which company has the highest net margin?\n" +
        "  - How healthy is Tesla?\n" +
        "  - Show a chart of revenue\n" +
        "  - What about Microsoft?  (follow-ups remember what we were discussing)\n" +
        "  Note: I report figures from company filings. This is not investment advice.";
    }

    // ---------------- main entry point ----------------
    respond(message) {
      const text = message.toLowerCase().replace(/[^\w\s'%-]/g, " ").split(/\s+/).filter(Boolean).join(" ");
      if (!text) return "Please type a question, or type 'help' to see what I can do.";

      const outside = this.findOutOfScope(text);
      let companies = this.findCompanies(text);
      let metric = this.findMetric(text);
      let year = this.findYear(text);
      let intent = this.findIntent(text);

      if (intent === "help") return this.help();
      if (intent === "advice") {
        let reply = "I can't give investment advice or comment on share prices. I report historical figures " +
          "from company 10-K filings, which you may find useful alongside advice from a qualified financial adviser.";
        if (companies.length) {
          reply += `\n\nHere are the facts for ${companies[0]}:\n` + this.answerSummary(companies[0]);
          this.memory = { companies: companies.slice(0, 1), metric: null, year: this.latestYear, intent: "summary" };
        }
        return reply;
      }
      if (intent === "goodbye") return "Goodbye! Thanks for using the GFC Financial Chatbot.";
      if (intent === "thanks" && !(companies.length || metric)) return "You're welcome. Ask me anything else about Microsoft, Tesla or Apple.";
      if (intent === "greeting" && !(companies.length || metric)) return "Hello! I'm the GFC Financial Chatbot. Ask me about Microsoft, Tesla or Apple, or type 'help'.";
      if (outside && !companies.length)
        return `I don't have data for ${outside}. I currently cover Microsoft, Tesla and Apple for FY${this.years[0]} to FY${this.latestYear}.`;
      if (typeof year === "string")
        return `My data covers FY${this.years[0]} to FY${this.latestYear}, so I can't answer for ${year.split(":")[1]}. I won't guess figures I haven't verified.`;

      if (intent === "greeting" || intent === "thanks") intent = null;
      if (!(companies.length || metric || year || intent))
        return "Sorry, I didn't understand that. I answer questions about the financial performance of Microsoft, Tesla and Apple. Type 'help' for examples.";

      const cue = ["what about", "how about", "and ", "what of", "same for"].some(c => text.startsWith(c));
      const partial = !(companies.length && metric);
      const isFollowUp = !!this.memory.intent && intent === null && (cue || partial);

      if (!companies.length && this.memory.companies.length && (isFollowUp || ["change", "trend", "value"].includes(intent)))
        companies = this.memory.companies;
      if (!metric && intent !== "summary" && (isFollowUp || intent)) metric = this.memory.metric;
      if (year === null) year = isFollowUp && this.memory.year ? this.memory.year : this.latestYear;
      if (intent === null) intent = isFollowUp ? this.memory.intent : (metric ? "value" : null);

      let answer;
      if (intent === "summary" && companies.length && !(metric && !contains(text, "health")))
        answer = companies.map(c => this.answerSummary(c)).join("\n\n");
      else if (intent === "summary" && !companies.length)
        answer = this.companies.map(c => this.answerSummary(c)).join("\n\n");
      else if (!metric)
        return "I'm not sure which figure you mean. I can tell you about revenue, net income, assets, liabilities, operating cash flow, net margin, leverage or equity. Type 'help' for examples.";
      else if (intent === "chart") answer = this.answerChart(companies, metric);
      else if ((intent === "change" || intent === "trend") && !companies.length) {
        companies = this.companies.slice();
        answer = companies.map(c => intent === "change" ? this.answerChange(c, metric, year) : this.answerTrend(c, metric)).join("\n\n");
      } else if (intent === "compare" && this.K.METRICS[metric].growth &&
                 ["grew", "grow", "growth", "fastest", "slowest", "quickest", "growing"].some(w => contains(text, w)))
        answer = this.answerGrowthRanking(companies, metric, text);
      else if (intent === "compare" || (companies.length >= 2 && (intent === null || intent === "value")) || !companies.length) {
        answer = this.answerCompare(companies, metric, year, text); intent = "compare";
      } else if (intent === "trend") answer = companies.map(c => this.answerTrend(c, metric)).join("\n\n");
      else if (intent === "change") answer = companies.map(c => this.answerChange(c, metric, year)).join("\n\n");
      else { answer = companies.map(c => this.answerValue(c, metric, year)).join("\n\n"); intent = "value"; }

      this.memory = { companies, metric, year, intent };
      if (this.suggestions) {
        const mt = answer.match(/\n  1\. (\w+):/);
        const lead = mt ? mt[1] : (companies.length ? companies[0] : null);
        answer += this.suggest(intent, lead ? [lead] : companies, metric);
      }
      return answer;
    }
  }

  root.GFCChatbot = { FinancialChatbot, formatMoney };
  if (typeof module !== "undefined" && module.exports) module.exports = { FinancialChatbot, formatMoney };
})(typeof window !== "undefined" ? window : globalThis);
