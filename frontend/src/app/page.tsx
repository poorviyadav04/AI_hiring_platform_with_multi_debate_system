import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      {/* Hero */}
      <section className="relative flex flex-col items-center justify-center px-4 py-24 text-center sm:py-32">
        {/* Gradient glow */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/2">
            <div className="h-[500px] w-[800px] rounded-full bg-gradient-to-br from-emerald-600/20 via-cyan-600/10 to-transparent blur-3xl" />
          </div>
        </div>

        <div className="relative z-10 flex flex-col items-center gap-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-4 py-1.5 text-sm text-emerald-400">
            <span className="relative flex size-2">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
            </span>
            AI-Powered Analysis
          </div>

          <h1 className="max-w-3xl text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl">
            AI-Powered{" "}
            <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              Hiring Intelligence
            </span>
          </h1>

          <p className="max-w-xl text-lg text-zinc-400">
            Whether you are looking for your next role or building your team,
            HireScope AI gives you data-driven insights powered by multi-agent
            analysis.
          </p>
        </div>
      </section>

      {/* CTA Cards */}
      <section className="mx-auto w-full max-w-5xl px-4 pb-16">
        <div className="grid gap-6 md:grid-cols-2">
          {/* Candidate card */}
          <Link href="/candidate" className="group">
            <div className="relative flex h-full flex-col gap-4 overflow-hidden rounded-2xl border border-white/10 bg-zinc-900/60 p-8 transition-all duration-300 hover:border-emerald-500/30 hover:shadow-lg hover:shadow-emerald-500/5">
              <div className="flex size-12 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 text-xl font-bold text-white">
                C
              </div>
              <h2 className="text-2xl font-bold text-white">
                I&apos;m a Candidate
              </h2>
              <p className="text-zinc-400">
                Check where you stand against any job. Upload your resume, paste
                the JD, and get instant feedback with a personalized improvement
                roadmap.
              </p>
              <div className="mt-auto flex items-center gap-2 text-sm font-medium text-emerald-400 transition-transform group-hover:translate-x-1">
                Get Started
                <svg
                  className="size-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"
                  />
                </svg>
              </div>
            </div>
          </Link>

          {/* Hiring card */}
          <Link href="/hiring" className="group">
            <div className="relative flex h-full flex-col gap-4 overflow-hidden rounded-2xl border border-white/10 bg-zinc-900/60 p-8 transition-all duration-300 hover:border-cyan-500/30 hover:shadow-lg hover:shadow-cyan-500/5">
              <div className="flex size-12 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 text-xl font-bold text-white">
                H
              </div>
              <h2 className="text-2xl font-bold text-white">
                I&apos;m Hiring
              </h2>
              <p className="text-zinc-400">
                Evaluate candidates at scale. Upload resumes, get AI-powered
                rankings with GitHub verification and multi-agent debate
                analysis.
              </p>
              <div className="mt-auto flex items-center gap-2 text-sm font-medium text-cyan-400 transition-transform group-hover:translate-x-1">
                Get Started
                <svg
                  className="size-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"
                  />
                </svg>
              </div>
            </div>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto w-full max-w-5xl px-4 pb-24">
        <h3 className="mb-8 text-center text-sm font-semibold uppercase tracking-wider text-zinc-500">
          How it works
        </h3>
        <div className="grid gap-6 sm:grid-cols-3">
          {[
            {
              title: "Resume Analysis",
              desc: "AI extracts skills, experience, and education from your resume and compares them against the job description.",
              icon: (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
                />
              ),
            },
            {
              title: "Multi-Agent Debate",
              desc: "Four AI agents - Evaluator, Advocate, Skeptic, and Moderator - debate each candidate to produce balanced assessments.",
              icon: (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3a49.5 49.5 0 0 1-4.02-.163 2.115 2.115 0 0 1-1.23-.578m0 0a2.125 2.125 0 0 1-.476-1.116 49 49 0 0 1-.118-3.3 2.122 2.122 0 0 1 1.594-2.09c1.322-.283 2.68-.43 4.06-.43 1.38 0 2.74.147 4.06.43a2.122 2.122 0 0 1 1.594 2.09 49 49 0 0 1-.194 4.074m-6.5-3.966a49 49 0 0 0-3.97-.194c-1.38 0-2.74.147-4.06.43A2.122 2.122 0 0 0 2.25 9.81a49 49 0 0 0 .118 3.3c.04.476.22.912.533 1.26m0 0 3.099 3.099"
                />
              ),
            },
            {
              title: "GitHub Verification",
              desc: "Validates claimed skills against real GitHub activity, detecting discrepancies and generating trust scores.",
              icon: (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z"
                />
              ),
            },
          ].map((f, i) => (
            <div
              key={i}
              className="flex flex-col gap-3 rounded-xl border border-white/5 bg-zinc-900/40 p-6"
            >
              <svg
                className="size-8 text-emerald-400"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                {f.icon}
              </svg>
              <h4 className="font-semibold text-white">{f.title}</h4>
              <p className="text-sm leading-relaxed text-zinc-400">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
