/** The title of step 1, with each mock's own sentence under it. */
export function ResumeHeading() {
  return (
    <>
      <h1 className="heading text-[36px] leading-[1.05] md:text-[52px] md:leading-none">
        Start with your resume.
      </h1>
      <p className="max-w-[600px] text-ink-2 max-md:hidden">
        It’s how NxtRole scores jobs and tailors applications. Your name, phone and email are
        removed before any AI reads it.
      </p>
      <p className="text-ink-2 md:hidden">
        NxtRole reads it once to learn your skills and experience. It only uses facts you’ve
        confirmed.
      </p>
    </>
  );
}
