// const MISTRAL_API_KEY = process.env.MISTRAL_API_KEY;

// async function generateAI(prompt) {
//   const response = await fetch("https://api.mistral.ai/v1/chat/completions", {
//     method: "POST",
//     headers: {
//       "Authorization": `Bearer ${MISTRAL_API_KEY}`,
//       "Content-Type": "application/json",
//     },
//     body: JSON.stringify({
//       model: "mistral-small-latest", // free tier model
//       messages: [{ role: "user", content: prompt }],
//       temperature: 0.7,
//       max_tokens: 800,
//     }),
//   });

//   const data = await response.json();

//   if (data.error) throw new Error("Mistral API error: " + data.error.message);

//   return data.choices[0]?.message?.content?.trim() || "";
// }

// module.exports = { generateAI, generateWithMistral: generateAI }


const MISTRAL_API_KEY = process.env.MISTRAL_API_KEY;

async function generateAI(prompt) {
  if (!MISTRAL_API_KEY) {
    throw new Error("MISTRAL_API_KEY is missing in backend .env");
  }

  const response = await fetch(
    "https://api.mistral.ai/v1/chat/completions",
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${MISTRAL_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "mistral-small-latest",
        messages: [{ role: "user", content: prompt }],
        temperature: 0.7,
        max_tokens: 800,
      }),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    const message =
      data?.error?.message ||
      data?.message ||
      `HTTP ${response.status}`;

    throw new Error(`Mistral API error: ${message}`);
  }

  const content = data?.choices?.[0]?.message?.content;

  if (typeof content !== "string" || !content.trim()) {
    throw new Error(
      "Mistral returned no text. Check the model response format."
    );
  }

  return content.trim();
}

module.exports = {
  generateAI,
  generateWithMistral: generateAI,
};
