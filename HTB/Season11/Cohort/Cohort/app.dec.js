/* Cohort Analytics - client-side rendered site.
   The page DOM is built here at runtime (the HTML shell ships empty). Content
   render + scroll-reveal + the Client Insights source validator all live here. */
(function () {
  "use strict";

  var HEADER = function (page) {
    var right = page === "portal"
      ? '<a class="btn btn-ghost" href="/">Back to site</a>'
      : '<a class="btn btn-ghost" href="/portal.html">Client Insights</a>';
    return ''
      + '<header><div class="wrap nav">'
      + '<a class="brand" href="/"><span class="mark" aria-hidden="true"></span> Cohort Analytics</a>'
      + '<nav class="nav-links" aria-label="Primary">'
      + '<a href="/#services">Services</a><a href="/#approach">Approach</a>'
      + '<a href="/#results">Results</a><a href="/#team">Team</a></nav>'
      + '<div class="nav-cta">' + right + '</div>'
      + '</div></header>';
  };

  var FOOTER = ''
    + '<footer><div class="wrap"><div class="foot">'
    + '<div><a class="brand" href="/" style="color:var(--ink)"><span class="mark" aria-hidden="true"></span> Cohort Analytics</a>'
    + '<p style="margin-top:14px;max-width:34ch;">Retention intelligence for subscription businesses.</p></div>'
    + '<div class="foot-cols">'
    + '<div class="foot-col"><b>Company</b><a href="/#services">Services</a><a href="/#approach">Approach</a><a href="/#team">Team</a></div>'
    + '<div class="foot-col"><b>Clients</b><a href="/portal.html">Client Insights</a></div>'
    + '</div></div>'
    + '<p style="margin-top:34px;color:var(--ink-faint);font-size:0.84rem;">&copy; Cohort Analytics. Registered in the United Kingdom.</p>'
    + '</div></footer>';

  var HOME = ''
    + '<section class="hero"><div class="wrap hero-grid"><div>'
    + '<h1>Retention is a measurement problem before it is a growth problem.</h1>'
    + '<p class="lede">We help subscription teams read their cohort data honestly, find where accounts quietly slip away, and decide what to fix first.</p>'
    + '<div class="hero-cta"><a class="btn btn-primary" href="/portal.html">Open Client Insights</a>'
    + '<a class="btn btn-ghost" href="/#approach">How we work</a></div></div>'
    + '<div class="hero-figure reveal"><div class="viz">'
    + '<div class="viz-head"><span>Retention by cohort</span><span class="viz-tag">Q2</span></div>'
    + '<div class="viz-bars"><i style="--h:62%"></i><i style="--h:77%"></i><i style="--h:70%"></i><i style="--h:88%"></i><i style="--h:81%"></i><i style="--h:93%"></i></div>'
    + '<div class="viz-axis"><span>Jan</span><span>Feb</span><span>Mar</span><span>Apr</span><span>May</span><span>Jun</span></div>'
    + '</div></div>'
    + '</div></section>'

    + '<section id="services" class="services"><div class="wrap">'
    + '<div class="section-head"><p class="kicker">What we do</p>'
    + '<h2>Four engagements, one question: who stays, and why.</h2></div>'
    + '<div class="svc-grid">'
    + '<div class="svc lead reveal"><div><div class="num">01</div><h3>Cohort and retention modelling</h3>'
    + '<p>We rebuild your retention curves from raw events, separate true churn from billing noise, and show which acquisition cohorts actually hold.</p></div>'
    + '<p style="color:var(--ink-faint);font-size:0.9rem;margin-top:24px;">Most engagements start here, with a two-week read of your existing data.</p></div>'
    + '<div class="svc reveal"><div class="num">02</div><h3>Churn forecasting</h3><p>Survival models that estimate account-level risk on a rolling basis, scored against revenue rather than logins.</p></div>'
    + '<div class="svc reveal"><div class="num">03</div><h3>Activation analytics</h3><p>We trace the first-30-day paths that predict a renewal, then tell you which onboarding steps are worth the effort.</p></div>'
    + '<div class="svc reveal"><div class="num">04</div><h3>Reporting that gets read</h3><p>A small set of dashboards your operators trust, wired to the same definitions finance uses, refreshed on a schedule.</p></div>'
    + '<div class="svc reveal"><div class="num">05</div><h3>Source review</h3><p>Before we model anything, we validate every feed you point us at, so the numbers reconcile from day one.</p></div>'
    + '</div></div></section>'

    + '<section id="approach"><div class="wrap split">'
    + '<div class="split-media reveal viz-curve" role="img" aria-label="Illustrative retention trend"></div>'
    + '<div><h2>We work in the open, on your data, with definitions you can defend.</h2>'
    + '<p class="lede" style="margin-top:16px;">No black boxes. Every model we ship comes with the query that produced it and a plain-language note on what it assumes.</p>'
    + '<div class="steps">'
    + '<div class="step reveal"><b>A</b><p>Connect your warehouse or a read-only export, and agree on what a retained account means.</p></div>'
    + '<div class="step reveal"><b>B</b><p>Reconcile the raw feed against billing so the cohort sizes match the invoices.</p></div>'
    + '<div class="step reveal"><b>C</b><p>Model, review together, and hand back the notebook so your team can keep running it.</p></div>'
    + '</div></div></div></section>'

    + '<section id="results" class="results"><div class="wrap">'
    + '<div class="section-head"><p class="kicker">Outcomes</p><h2>What teams tend to see in the first two quarters.</h2></div>'
    + '<div class="metrics">'
    + '<div class="metric reveal"><div class="figure">20 to 40%</div><div class="label">fewer accounts misclassified as churned once billing is reconciled</div></div>'
    + '<div class="metric reveal"><div class="figure">3 weeks</div><div class="label">from kickoff to a retention model the operating team trusts</div></div>'
    + '<div class="metric reveal"><div class="figure">1 source</div><div class="label">of truth for cohort definitions, shared by product and finance</div></div>'
    + '</div>'
    + '<p class="note">Figures are representative ranges from recent engagements, not guarantees. Results depend on data quality and how quickly definitions are agreed.</p>'
    + '</div></section>'

    + '<section id="team"><div class="wrap">'
    + '<div class="section-head"><h2>A small team that does the analysis itself.</h2>'
    + '<p>No layered account management. The people who scope your engagement are the ones in your data.</p></div>'
    + '<div class="people">'
    + '<div class="person reveal"><span class="avatar" aria-hidden="true">MQ</span><div><strong>Mara Quinteros</strong><div class="role">Founder, retention modelling</div></div></div>'
    + '<div class="person reveal"><span class="avatar" aria-hidden="true">DO</span><div><strong>Devin Oyelaran</strong><div class="role">Analytics engineering</div></div></div>'
    + '</div></div></section>'

    + '<section class="cta-band"><div class="wrap inner">'
    + '<h2>Have a feed you want validated?</h2>'
    + '<a class="btn btn-primary" href="/portal.html">Open Client Insights</a>'
    + '</div></section>';

  var PORTAL = ''
    + '<section class="portal"><div class="wrap">'
    + '<div class="section-head" style="margin-bottom:36px;"><span class="tag">Client Insights</span>'
    + '<h2 style="margin-top:14px;">Register a report source URL</h2>'
    + '<p>Point us at a data feed and we fetch it once to confirm it is reachable and returns a format we recognise. Validated sources are queued for reconciliation against your billing export.</p></div>'
    + '<div class="portal-grid"><div class="panel">'
    + '<form id="validate-form" novalidate>'
    + '<div class="field" id="f-url"><label for="url">Source URL</label>'
    + '<input id="url" name="url" type="url" inputmode="url" placeholder="https://reports.example.htb/exports/retention.csv" autocomplete="off" spellcheck="false">'
    + '<span class="help">The endpoint we should fetch. Public report endpoints only.</span>'
    + '<span class="err" id="e-url">Enter a source URL to validate.</span></div>'
    + '<div class="field"><label for="format">Expected format</label>'
    + '<select id="format" name="format"><option value="csv">CSV</option><option value="json">JSON</option><option value="ndjson">NDJSON</option><option value="parquet">Parquet</option></select>'
    + '<span class="help">Used to sanity-check the response before reconciliation.</span></div>'
    + '<button class="btn btn-primary" type="submit" id="submit-btn" style="width:100%;justify-content:center;">Validate source</button>'
    + '</form>'
    + '<div class="result" id="result" aria-live="polite">'
    + '<div class="rhead"><span class="dot" id="r-dot"></span><span id="r-title">Validation result</span></div>'
    + '<div class="skeleton" id="r-skel" hidden><i></i><i></i><i></i></div>'
    + '<pre id="r-body"></pre></div>'
    + '</div>'
    + '<aside class="portal-aside">'
    + '<h3>What validation checks</h3><ul>'
    + '<li>The endpoint resolves and responds within a few seconds.</li>'
    + '<li>The response status and content type look like a real export.</li>'
    + '<li>We capture a short preview so you can confirm it is the right feed.</li></ul>'
    + '<h3 style="margin-top:28px;">Notes</h3><ul>'
    + '<li>For security, internal and loopback addresses are rejected.</li>'
    + '<li>We never store credentials in the URL. Use a signed link or an allow-listed IP instead.</li>'
    + '<li>Validation does not import data. Reconciliation is a separate, scheduled step.</li></ul>'
    + '</aside></div></div></section>';

  function initReveal() {
    var els = document.querySelectorAll(".reveal");
    if (!els.length) return;
    if (!("IntersectionObserver" in window)) {
      els.forEach(function (el) { el.classList.add("in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { threshold: 0.18 });
    els.forEach(function (el) { io.observe(el); });
  }

  function initForm() {
    var form = document.getElementById("validate-form");
    if (!form) return;
    var urlField = document.getElementById("f-url");
    var urlInput = document.getElementById("url");
    var btn = document.getElementById("submit-btn");
    var result = document.getElementById("result");
    var rdot = document.getElementById("r-dot");
    var rtitle = document.getElementById("r-title");
    var rskel = document.getElementById("r-skel");
    var rbody = document.getElementById("r-body");

    function setBusy(b) { btn.disabled = b; btn.textContent = b ? "Validating..." : "Validate source"; }
    function show(ok, title, body) {
      rskel.hidden = true;
      rdot.className = "dot" + (ok ? "" : " bad");
      rtitle.textContent = title;
      rbody.textContent = body;
      result.classList.add("show");
    }

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var url = (urlInput.value || "").trim();
      if (!url) { urlField.classList.add("invalid"); urlInput.focus(); return; }
      urlField.classList.remove("invalid");
      result.classList.add("show");
      rbody.textContent = "";
      rtitle.textContent = "Validating source...";
      rdot.className = "dot";
      rskel.hidden = false;
      setBusy(true);

      fetch("/api/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ url: url, format: document.getElementById("format").value })
      })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          j = j || {};
          if (j.ok) {
            var head = "Reachable. HTTP " + (j.fetched_status != null ? j.fetched_status : "?") +
                       (j.content_type ? " (" + j.content_type + ")" : "");
            show(true, head, (j.preview != null ? j.preview : "") || "(empty response body)");
          } else {
            show(false, "Could not validate source", j.message || "The source could not be validated.");
          }
        })
        .catch(function () { show(false, "Validation service unavailable", "We could not reach the validation service. Please try again shortly."); })
        .finally(function () { setBusy(false); });
    });

    urlInput.addEventListener("input", function () { urlField.classList.remove("invalid"); });
  }

  function render() {
    var root = document.getElementById("app");
    if (!root) return;
    var page = root.getAttribute("data-page") || "home";
    var main = page === "portal" ? PORTAL : HOME;
    root.innerHTML = HEADER(page) + "<main>" + main + "</main>" + FOOTER;
    root.removeAttribute("aria-busy");
    initReveal();
    if (page === "portal") initForm();
    if (window.location.hash) {
      var t = document.querySelector(window.location.hash);
      if (t) t.scrollIntoView();
    }
  }

  if (document.readyState !== "loading") render();
  else document.addEventListener("DOMContentLoaded", render);
})();
