from flask import Flask, render_template_string, request
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
current_stage = 1
hits = 0
total = 0
training = False

TEMPLATE = """
<!DOCTYPE html>
<html>
  <head>
    <title>7碼預測器（hotplus-v2強化補碼）</title>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
  </head>
  <body style="max-width: 400px; margin: auto; padding-top: 50px; text-align: center; font-family: sans-serif;">
    <h2>7碼預測器（hotplus-v2強化補碼）</h2>
    <form method="POST">
      <div>
        <input type="number" name="first" id="first" placeholder="冠軍號碼" required style="width: 80%; padding: 8px;" oninput="handleInput(this, 'second')"><br><br>
        <input type="number" name="second" id="second" placeholder="亞軍號碼" required style="width: 80%; padding: 8px;" oninput="handleInput(this, 'third')"><br><br>
        <input type="number" name="third" id="third" placeholder="季軍號碼" required style="width: 80%; padding: 8px;"><br><br>
        <button type="submit" style="padding: 10px 20px;">提交</button>
      </div>
    </form>
    <br>
    <a href="/toggle"><button>{{ toggle_text }}</button></a>
    {% if training %}
      <div><strong>訓練中...</strong></div>
      <div>命中率：{{ stats }}</div>
      <div>目前階段：第 {{ stage }} 關</div>
    {% endif %}
    {% if last_champion %}
      <br><div><strong>上期冠軍號碼：</strong>{{ last_champion }}</div>
      <div><strong>是否命中：</strong>{{ hit }}</div>
      <div><strong>上期預測號碼：</strong>{{ last_prediction }}</div>
    {% endif %}
    {% if result %}
      <br><div><strong>下期預測號碼：</strong> {{ result }}</div>
    {% endif %}
    <br>
    <div style="text-align: left;">
      <strong>最近輸入紀錄：</strong>
      <ul>
        {% for row in history %}
          <li>{{ row }}</li>
        {% endfor %}
      </ul>
    </div>
    <script>
      function handleInput(current, nextId) {
        let val = parseInt(current.value);
        if (val === 0) {
          current.value = 10;
        }
        if (current.value.length >= 1 && val >= 1 && val <= 10) {
          setTimeout(() => {
            document.getElementById(nextId).focus();
          }, 50);
        }
      }
    </script>
  </body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    global hits, total, stage, training, current_stage
    result = None
    last_champion = None
    last_prediction = None
    hit = None

    if request.method == "POST":
        try:
            first = int(request.form.get("first"))
            second = int(request.form.get("second"))
            third = int(request.form.get("third"))
            first = 10 if first == 0 else first
            second = 10 if second == 0 else second
            third = 10 if third == 0 else third
            current = [first, second, third]
            history.append(current)

            if len(predictions) >= 1:
                last_prediction = predictions[-1]
                last_champion = current[0]
                if last_champion in last_prediction:
                    hit = "命中"
                    if training:
                        hits += 1
                        current_stage = 1
                else:
                    hit = "未命中"
                    if training:
                        current_stage += 1
                if training:
                    total += 1

            if len(history) >= 3:
                prediction = generate_prediction()
                predictions.append(prediction)
                result = prediction
            else:
                result = "請至少輸入三期資料後才可預測"

        except:
            result = "格式錯誤，請輸入 1~10 的整數"

    toggle_text = "關閉訓練模式" if training else "啟動訓練模式"
    return render_template_string(TEMPLATE, result=result, history=history[-10:],
                                  last_champion=last_champion, last_prediction=last_prediction,
                                  hit=hit, training=training, toggle_text=toggle_text,
                                  stats=f"{hits} / {total}" if training else None,
                                  stage=current_stage if training else None)

@app.route("/toggle")
def toggle():
    global training, hits, total, current_stage
    training = not training
    if training:
        hits = 0
        total = 0
        current_stage = 1
    return "<script>window.location.href='/'</script>"

def generate_prediction():
    recent = history[-3:]
    flat = [n for g in recent for n in g]
    # 熱號：前一期取出 3 碼，隨機選 2
    hot_pool = list(dict.fromkeys(history[-1]))[:3]
    hot = random.sample(hot_pool, k=min(2, len(hot_pool)))
    # 動態熱號：最近三期中，排除熱號後統計出現次數
    dyn_flat = [n for g in recent for n in g if n not in hot]
    freq = {n: dyn_flat.count(n) for n in set(dyn_flat)}
    max_count = max(freq.values()) if freq else 0
    dyn_pool = [n for n in freq if freq[n] == max_count]
    dynamic = random.sample(dyn_pool, k=min(2, len(dyn_pool)))
    # 補碼：從 1~10 扣除以上選號
    used = set(hot + dynamic)
    remain = [n for n in range(1, 11) if n not in used]
    random.shuffle(remain)
    extra = remain[:3]
    return sorted(hot + dynamic + extra)

if __name__ == "__main__":
    app.run(debug=True)
