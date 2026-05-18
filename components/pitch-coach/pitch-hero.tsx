"use client"

export function PitchHero() {
  return (
    <section className="px-4 md:px-8 pt-28 pb-12">
      <div className="max-w-5xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-purple-500/20 bg-white/5 px-4 py-2 text-sm text-purple-200 backdrop-blur-sm">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-purple-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-purple-500" />
          </span>
          AI pitch coaching powered by your Flask models
        </div>

        <h1 className="mt-6 text-4xl font-semibold tracking-tight text-white md:text-6xl">
          Practice your pitch with
          <span className="bg-gradient-to-r from-purple-300 via-violet-300 to-fuchsia-300 bg-clip-text text-transparent"> live model feedback</span>
        </h1>

        <p className="mx-auto mt-5 max-w-2xl text-sm leading-7 text-slate-300 md:text-lg">
          This page connects directly to your backend in <span className="text-white">backend/app.py</span> to analyze emotion and stress from webcam frames, while keeping the ScaleUp visual style.
        </p>
      </div>
    </section>
  )
}
