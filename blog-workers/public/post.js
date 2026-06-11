(function () {
  const reactionsEl = document.getElementById("reactions");
  if (reactionsEl) {
    const postId = reactionsEl.dataset.postId;
    const csrf = reactionsEl.dataset.csrf;

    reactionsEl.querySelectorAll(".reaction-btn").forEach(function (btn) {
      btn.addEventListener("click", async function () {
        const kind = btn.dataset.kind;
        try {
          const res = await fetch("/api/post/" + postId + "/react", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRF-Token": csrf,
            },
            body: JSON.stringify({ kind: kind }),
          });
          const data = await res.json();
          if (!data.ok) return;
          document.getElementById("like-count").textContent = data.counts.like;
          document.getElementById("dislike-count").textContent = data.counts.dislike;
          document.getElementById("like-btn").classList.toggle("active", data.reaction === "like");
          document.getElementById("dislike-btn").classList.toggle("active", data.reaction === "dislike");
        } catch (e) {
          /* ignore */
        }
      });
    });
  }

  const commentForm = document.getElementById("comment-form");
  if (commentForm) {
    const postId = commentForm.dataset.postId;
    const csrf = commentForm.dataset.csrf;
    const errorEl = document.getElementById("comment-error");
    const listEl = document.getElementById("comment-list");

    commentForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const body = document.getElementById("comment-body").value;
      errorEl.hidden = true;
      try {
        const res = await fetch("/api/post/" + postId + "/comment", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrf,
          },
          body: JSON.stringify({ body: body }),
        });
        const data = await res.json();
        if (!data.ok) {
          errorEl.textContent = data.error;
          errorEl.hidden = false;
          return;
        }
        const li = document.createElement("li");
        li.className = "comment";
        li.dataset.commentId = String(data.comment.id);
        const meta = document.createElement("div");
        meta.className = "comment-meta";
        const author = document.createElement("strong");
        author.textContent = data.comment.author;
        const time = document.createElement("time");
        time.dateTime = data.comment.created_at;
        time.textContent = data.comment.created_at;
        meta.appendChild(author);
        meta.appendChild(time);
        const p = document.createElement("p");
        p.className = "comment-body";
        p.textContent = data.comment.body;
        li.appendChild(meta);
        li.appendChild(p);
        listEl.appendChild(li);
        document.getElementById("comment-body").value = "";
      } catch (err) {
        errorEl.textContent = "Something went wrong.";
        errorEl.hidden = false;
      }
    });
  }

  const deleteBtn = document.getElementById("delete-btn");
  if (deleteBtn) {
    deleteBtn.closest("form").addEventListener("submit", function (e) {
      if (!confirm("Delete this post permanently?")) {
        e.preventDefault();
      }
    });
  }
})();
