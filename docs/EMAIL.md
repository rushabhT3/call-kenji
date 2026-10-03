# Email kit: sending Call Kenji

Everything needed to send Call Kenji to a founder or CEO, or to HR and recruiters: the links,
the trailer GIF to put at the top of the email, three subject lines and a short body for each.

## Links

| What | Link |
| --- | --- |
| Trailer | https://call-kenji.call-kenji-web.workers.dev/trailer |
| Kenji's Universe (zoomable pitch) | https://call-kenji.call-kenji-web.workers.dev/pitch |
| Live demo: call Kenji in the browser | https://call-kenji.call-kenji-web.workers.dev/ |
| How it's built | https://call-kenji.call-kenji-web.workers.dev/features |

## The trailer GIF

Gmail and Outlook will not play a video inside an email, so the email carries a short looping GIF
that links to the trailer page. Gmail plays the GIF. Older desktop Outlook shows only its first
frame, so the first frame has to make sense on its own: the title and the play button, readable
without the motion.

```html
<a href="https://call-kenji.call-kenji-web.workers.dev/trailer">
  <img
    src="https://call-kenji.call-kenji-web.workers.dev/trailer/kenji-email.gif"
    width="600"
    alt="Call Kenji trailer: a Japanese voice agent that shows its reasoning live. Click to watch."
    style="display: block; max-width: 100%; height: auto; border: 0"
  />
</a>
```

### Putting it in a Gmail message

1. Open https://call-kenji.call-kenji-web.workers.dev/trailer/kenji-email.gif in the browser,
   right-click the GIF and copy the image (or save it and use Insert photo).
2. Paste it at the top of the message, above the first line.
3. Click the GIF once, press Ctrl+K (Cmd+K on a Mac) and paste the trailer link,
   https://call-kenji.call-kenji-web.workers.dev/trailer.
4. Send a test to yourself and check the GIF plays and the click opens the trailer.

The voice server scales to zero when nobody is using it. Open the live demo yourself a minute
before you send, so the first person to click does not wait for it to wake.

## To founders and CEOs

Subject lines:

1. A Japanese voice agent that answers in about 0.7 s on a model that needs 2 to 6
2. Call Kenji: watch a voice agent think, live
3. Turn-taking, compliance and latency, on screen in one voice agent

Body:

> Hi {first name},
>
> I built Call Kenji, a Japanese debt-collection voice agent that shows its reasoning live while
> you talk to it. It starts answering in about 0.7 seconds (p50) on a reasoning model that needs
> 2 to 6: rules answer the predictable turns, and every other turn opens at once while the model
> thinks. Compliance is code, not a prompt, so it cannot agree to a payment below the terms
> however hard you push.
>
> Trailer: https://call-kenji.call-kenji-web.workers.dev/trailer
> Call it yourself, no Japanese needed: https://call-kenji.call-kenji-web.workers.dev/
> Kenji's Universe: https://call-kenji.call-kenji-web.workers.dev/pitch
>
> Happy to walk you through it.
>
> Rushabh Trivedi

## To HR and recruiters

Subject lines:

1. Rushabh Trivedi: voice AI engineer, built Call Kenji end to end
2. The trailer for what I built: Call Kenji
3. Voice AI portfolio: a live Japanese voice agent you can call

Body:

> Hi {first name},
>
> I'm Rushabh Trivedi. I designed and built Call Kenji end to end: a Japanese voice agent for
> debt collection, with a live view of every decision it makes. It starts answering in about
> 0.7 seconds on a model that needs 2 to 6, passes 24 of 24 real-model conversation checks, and
> its rules have 100% line and branch test coverage.
>
> The quickest way in is the trailer: https://call-kenji.call-kenji-web.workers.dev/trailer
> Then call it in your browser, no Japanese needed: https://call-kenji.call-kenji-web.workers.dev/
> What I built and why: https://call-kenji.call-kenji-web.workers.dev/features
>
> I'd welcome the chance to talk about the role.
>
> Rushabh

## Before sending

- Open each link once: the trailer plays with sound, the pitch zooms, the live demo connects a
  call, and the features page loads.
- Check the GIF in a test email to yourself, in Gmail and, if you can, in Outlook.
- Replace {first name} and read the body once more for the person you are writing to.
