// // const { generateAI } = require("../services/gemini.service")
// const { generateAI } = require("../services/mistral.service")
// exports.generatePost = async(req,res)=>{

//   const { topic, tone, contentType } = req.body
 
//   const prompt = `
// You are a LinkedIn content creator. Write a ${contentType} LinkedIn post about: ${topic}
 
// Tone: ${tone}
 
// Rules you MUST follow:
// - Output ONLY the post text itself — no preamble, no "Here's your post", no "Sure!", no intro sentence, no commentary before or after
// - Start directly with the first line of the post (a hook, a question, a bold statement, or an emoji)
// - End with relevant hashtags on the last line
// - Do not wrap in quotes or markdown
 
// Now write the post:
// `
 
//   const post = await generateAI(prompt)
 
//   // Strip any leaked preamble lines as a safety net
//   const cleaned = post
//     .replace(/^(here'?s?|sure[,!]?|absolutely[,!]?|of course[,!]?|great[,!]?|below is|here is)[^\n]*\n?/gi, "")
//     .replace(/^(your (linkedin )?post|the post)[^\n]*\n?/gi, "")
//     .trim()
 
//   res.json({ post: cleaned })


// }


// ye abhi kiya

// const { generateWithMistral } = require("../services/mistral.service")
// const { generateWithGemini } = require("../services/gemini.service")

// exports.generatePost = async (req, res) => {
//   const { topic, tone, contentType } = req.body

//   const prompt = `
// You are a LinkedIn content creator. Write a ${contentType} LinkedIn post about: ${topic}

// Tone: ${tone}

// Rules you MUST follow:
// - Output ONLY the post text itself — no preamble, no "Here's your post", no "Sure!", no intro sentence, no commentary before or after
// - Start directly with the first line of the post (a hook, a question, a bold statement, or an emoji)
// - End with relevant hashtags on the last line
// - Do not wrap in quotes or markdown

// Now write the post:
// `

//   let raw = ""

//   try {
//     console.log("[LinkedIn Post] Trying Mistral...")
//     raw = await generateWithMistral(prompt)
//   } catch (mistralErr) {
//     console.warn("[LinkedIn Post] Mistral failed:", mistralErr.message, "— switching to Gemini")
//     raw = await generateWithGemini(prompt)
//   }

//   const post = raw
//     .replace(/^(here'?s?|sure[,!]?|absolutely[,!]?|of course[,!]?|great[,!]?|below is|here is)[^\n]*\n?/gi, "")
//     .replace(/^(your (linkedin )?post|the post)[^\n]*\n?/gi, "")
//     .trim()

//   res.json({ post })
// }

// yaha tak


const { generateWithMistral } = require("../services/mistral.service");
const { generateWithGemini } = require("../services/gemini.service");

exports.generatePost = async (req, res) => {
  const { topic, tone, contentType } = req.body;

  if (!topic?.trim()) {
    return res.status(400).json({
      error: "Topic is required",
    });
  }

  const prompt = `
You are a LinkedIn content creator. Write a ${contentType || "Short Post"}
LinkedIn post about: ${topic}

Tone: ${tone || "Professional"}

Rules:
- Output only the post text.
- Start directly with an engaging hook.
- End with relevant hashtags.
- Do not include a preamble or quotation marks.
`;

  let raw;

  try {
    console.log("[LinkedIn Post] Trying Mistral...");
    raw = await generateWithMistral(prompt);
  } catch (mistralErr) {
    console.error("[LinkedIn Post] Mistral failed:", mistralErr.message);

    try {
      console.log("[LinkedIn Post] Trying Gemini...");
      raw = await generateWithGemini(prompt);
    } catch (geminiErr) {
      console.error("[LinkedIn Post] Gemini failed:", geminiErr.message);

      return res.status(502).json({
        error: "Both AI providers failed to generate the post.",
        mistralError: mistralErr.message,
        geminiError: geminiErr.message,
      });
    }
  }

  const post = String(raw || "")
    .replace(
      /^(here'?s?|sure[,!]?|absolutely[,!]?|of course[,!]?|great[,!]?|below is|here is)[^\n]*\n?/i,
      ""
    )
    .replace(/^(your (linkedin )?post|the post)[^\n]*\n?/i, "")
    .trim();

  if (!post) {
    return res.status(502).json({
      error: "AI providers returned an empty post.",
    });
  }

  return res.json({ post });
};