import { z } from "zod/v3";
import { Stagehand } from "@browserbasehq/stagehand";
import dotenv from "dotenv";

// Load environment variables from .env file
dotenv.config({ path: "../.env" });

// Run with:  npx ts-node recipe.ts <recipeUrl>
const recipeUrl = process.argv[2];
if (!recipeUrl) {
  console.error("Please provide a recipe URL as an argument");
  process.exit(1);
}

(async () => {
  let stagehand: Stagehand | null = null;

  try {
    console.log("Initializing Stagehand...");
    // Initialize Stagehand
    stagehand = new Stagehand({
      env: "BROWSERBASE",
      apiKey: process.env.BROWSERBASE_API_KEY,
      projectId: process.env.BROWSERBASE_PROJECT_ID!,
      model: "anthropic/claude-3-7-sonnet-latest",
      // Your ANTHROPIC_API_KEY is automatically read from your .env
      // For how to configure different models, visit https://docs.stagehand.dev/configuration/models#first-class-models
    });

    console.log("Starting browser session...");
    await stagehand.init();
    const page = stagehand.context.pages()[0];

    console.log(`Navigating to: ${recipeUrl}`);
    await page.goto(recipeUrl, { waitUntil: "domcontentloaded" });

    console.log("Waiting for page to load...");

    console.log("Looking for recipe section...");
    const jumpToRecipe = await stagehand.observe(
      `find the clickable text, link, or button that says "jump to recipe"`
    );
    try {
      console.log("Attempting to click 'jump to recipe' button...");
      await stagehand.act(
        `Click the text, link, or button that says "Jump to recipe"`
      );
      console.log("Successfully clicked jump to recipe");
    } catch (error) {
      console.log(
        "Could not find 'jump to recipe' button, continuing anyway..."
      );
      console.log("Error details:", error);
      console.log("Scrolling down to find recipe content...");
      try {
        await stagehand.act(
          "scroll down to find the recipe ingredients and instructions"
        );
        console.log("Successfully scrolled to recipe content");
      } catch (scrollError) {
        console.log("Error scrolling:", scrollError);
      }
    }

    console.log("Extracting ingredients...");
    let ingredients;
    try {
      ingredients = await stagehand.extract(
        "Extract each bullet point underneath the ingredients header",
        z.array(
          z.object({
            ingredient: z.string(),
          })
        )
      );
    } catch (error) {
      console.log(
        "Failed to extract structured ingredients, trying simple text extraction..."
      );
      ingredients = await stagehand.extract(
        "Extract all the ingredients from the recipe as a simple string"
      );
    }

    console.log("Extracting recipe steps...");
    let steps;
    try {
      steps = await stagehand.extract(
        "Extract each numbered item underneath the instructions section"
      );
    } catch (error) {
      console.log(
        "Failed to extract structured steps, trying simple text extraction..."
      );
      steps = await stagehand.extract(
        "Extract all the cooking instructions from the recipe as a simple string"
      );
    }

    console.log("INGREDIENTS: ", ingredients);
    console.log("RECIPE INSTRUCTIONS: ", steps);
  } catch (error) {
    console.error("Error occurred:", error);
    if (error instanceof Error) {
      console.error("Error message:", error.message);
      console.error("Error stack:", error.stack);
    }
  } finally {
    if (stagehand) {
      console.log("Closing browser session...");
      try {
        await stagehand.close();
      } catch (closeError) {
        console.error("Error closing stagehand:", closeError);
      }
    }
  }
})().catch((error) => {
  console.error("Unhandled error:", error);
  process.exit(1);
});
