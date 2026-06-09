const posts = [
  {
    id: 1,
    title: "The Day the Letter Arrived",
    tag: "Stories",
    date: "Mar 14, 2026",
    excerpt: "How one late-night robotics project and a handwritten essay opened the door to MIT.",
    body: [
      "I refreshed my inbox at 6:14 PM on Pi Day, mostly out of habit. I wasn't expecting anything — most of my friends had already heard back from their schools, and I was still waiting.",
      "Then I saw it: a subject line from MIT Admissions that started with one word — \"Congratulations.\" I read it three times before it felt real.",
      "I'm Maya Chen, from a town of 9,000 people where I'm the only student in my grade who stayed after school to solder circuit boards. I built a water-quality sensor with an Arduino because the creek behind our high school kept turning cloudy every spring, and nobody could explain why.",
      "On weekends I taught basic Python at the public library to kids who had never touched a keyboard. My MIT essay wasn't about perfect grades — it was about that creek, about showing up when no one was watching, and about believing that fixing small problems in your own backyard can lead somewhere bigger.",
      "When I called my mom, I couldn't get the words out at first. She thought something was wrong. Then I read the email aloud, and we both cried in the kitchen while the rice cooker beeped in the background.",
      "MIT didn't accept a résumé. They accepted a person who was curious, stubborn, and willing to build things that mattered to her community. If you're waiting on your own letter — keep going. The work you're doing when no one is clapping might be exactly what they're looking for."
    ]
  },
  {
    id: 2,
    title: "Why Simple Tools Win",
    tag: "Tech",
    date: "Jun 5, 2026",
    excerpt: "In a world of frameworks and abstractions, sometimes a plain HTML file is all you need.",
    body: [
      "We live in an era of infinite tooling. Every new project starts with a dozen dependencies, a build pipeline, and a config file for every conceivable option.",
      "But complexity has a cost. It slows you down, hides bugs, and makes your project harder to understand six months later.",
      "Plain HTML, CSS, and JavaScript have been around for decades — and they're not going anywhere. They load instantly, work everywhere, and require zero build step.",
      "Next time you start a side project, ask yourself: do I really need all of this, or can I ship something today with what I already know?"
    ]
  },
  {
    id: 3,
    title: "The Art of Slow Mornings",
    tag: "Life",
    date: "May 28, 2026",
    excerpt: "How reclaiming the first hour of your day can change everything.",
    body: [
      "Most of us reach for our phones before our feet hit the floor. Emails, notifications, the endless scroll — the day starts in reactive mode before we've had a chance to think.",
      "A slow morning isn't about waking at 5 AM or meditating for an hour. It's about protecting a small window of time that's entirely yours.",
      "Make coffee. Read a few pages. Write three lines in a journal. Walk outside without headphones.",
      "That quiet space compounds. Decisions get clearer. Stress drops. You show up to the rest of the day as yourself, not as a response to whatever showed up in your inbox."
    ]
  },
  {
    id: 4,
    title: "Learning in Public",
    tag: "Creativity",
    date: "May 15, 2026",
    excerpt: "Sharing what you're learning isn't bragging — it's how ideas spread.",
    body: [
      "We often wait until we're experts before we share anything. We worry about looking foolish, about not having the full picture.",
      "But the people who learn fastest are the ones who document their process along the way. They write blog posts about things they just figured out. They ask questions out loud.",
      "Learning in public creates accountability, attracts collaborators, and helps others who are a step behind you.",
      "You don't need to be an authority. You just need to be one step ahead of someone else — and willing to say what you found."
    ]
  },
  {
    id: 5,
    title: "Notes on Building Habits",
    tag: "Life",
    date: "Apr 30, 2026",
    excerpt: "Small actions, repeated consistently, beat grand plans every time.",
    body: [
      "We overestimate what we can do in a day and underestimate what we can do in a year. The gap between who we are and who we want to be is usually closed by habits, not motivation.",
      "The best habits are almost embarrassingly small. One push-up. Two minutes of reading. Writing one sentence.",
      "Make it easy to start. Remove friction. Stack new habits onto existing ones — after I pour my coffee, I write one line.",
      "Miss a day? Start again tomorrow. Consistency matters more than perfection."
    ]
  }
];

const postList = document.getElementById("post-list");
const postContent = document.getElementById("post-content");
const views = {
  home: document.getElementById("home-view"),
  post: document.getElementById("post-view"),
  about: document.getElementById("about-view")
};

function showView(name) {
  Object.values(views).forEach(v => v.classList.remove("active"));
  views[name].classList.add("active");
  window.scrollTo(0, 0);
}

function renderPostList() {
  postList.innerHTML = posts.map(post => `
    <div class="post-card" data-id="${post.id}">
      <div class="meta">
        <span class="tag">${post.tag}</span>
        <span class="date">${post.date}</span>
      </div>
      <h2>${post.title}</h2>
      <p>${post.excerpt}</p>
    </div>
  `).join("");

  postList.querySelectorAll(".post-card").forEach(card => {
    card.addEventListener("click", () => openPost(Number(card.dataset.id)));
  });
}

function openPost(id) {
  const post = posts.find(p => p.id === id);
  if (!post) return;

  postContent.innerHTML = `
    <div class="meta">
      <span class="tag">${post.tag}</span>
      <span class="date">${post.date}</span>
    </div>
    <h1>${post.title}</h1>
    <p class="lead">${post.excerpt}</p>
    ${post.body.map(p => `<p>${p}</p>`).join("")}
  `;

  showView("post");
}

document.querySelectorAll("[data-view]").forEach(el => {
  el.addEventListener("click", e => {
    e.preventDefault();
    showView(el.dataset.view);
  });
});

renderPostList();
