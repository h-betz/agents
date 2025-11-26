import { z } from "zod/v3";
import { Stagehand } from "@browserbasehq/stagehand";

// Run with:  npx ts-node google_docs.ts
(async () => {
    // Initialize Stagehand
    const stagehand = new Stagehand({
      env: "BROWSERBASE",
      apiKey: process.env.BROWSERBASE_API_KEY,
      projectId: process.env.BROWSERBASE_PROJECT_ID!,
      model: "anthropic/claude-3-5-sonnet-20241022",
      // Your ANTHROPIC_API_KEY is automatically read from your .env
      // For how to configure different models, visit https://docs.stagehand.dev/configuration/models#first-class-models
  });
  await stagehand.init();
  const page = stagehand.context.pages()[0];
  await page.goto("https://docs.google.com");

  // Preview an action before taking it
  await stagehand.act("fill the email field with the value hhb311@gmail.com");
  await stagehand.act("click the next button");


  // Read the NPM install command
//   const { npmInstallCommand } = await stagehand.extract(
//     "Extract the NPM install command",
//     z.object({
//       npmInstallCommand: z.string(),
//     })
//   );
//   console.log(npmInstallCommand);
  
  await stagehand.close();
})().catch((error) => console.error(error.message));