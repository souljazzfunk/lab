# Asiandocs 1080p

Asiandocs の会員ページで動画を再生すると、画質が低い状態（よくあるのは 360p）から始まることがあります。この Chrome 拡張機能は、再生が始まったあとに画質を自動で **1080p** に切り替えます。実際の会員ページで、1080p に切り替わることを確認しています。

Git の知識は要りません。下の手順は、ZIP をダウンロードして Chrome に読み込むだけです。

## この拡張が何をするか

- 動画の画質を、自動で **1080p**（フルHD）にします。
- 一覧に 1080p が無いときは、**自動以外で一番高い画質**を選びます。
- **自動**、**オート**、**Auto** は選びません。

ボタンを人が押すのと同じように、画面に出ている画質の項目を押すだけです。動画ファイルをダウンロードしたり、ログイン情報を送ったりはしません。

## インストール

https://github.com/souljazzfunk/lab/releases/download/asiandocs-1080p-latest/asiandocs-1080p.zip

上のリンクは、この拡張機能だけの ZIP です。リポジトリ全体の ZIP ではありません。

### 1. ZIP をダウンロードする

上のリンクをブラウザで開きます。`asiandocs-1080p.zip` が保存されます。

### 2. 解凍する

ZIP を解凍します。できるフォルダは次のとおりです。

```text
asiandocs-1080p
├── manifest.json
└── （拡張機能のファイル）
```

Chrome に渡すのは、この **asiandocs-1080p** です。フォルダを開くと、すぐそこに `manifest.json` があります。

ひとつ外側のフォルダを選ぶと失敗します。Chrome は「拡張機能を読み込めませんでした」「マニフェストを読み込めませんでした。」と表示します。`manifest.json` が直接入っているフォルダを選び直してください。

解凍した場所は、あとから分かるところ（ドキュメントフォルダなど）にしてください。読み込んだあとに、このフォルダを消したり別の場所へ移したりすると、拡張機能は動かなくなります。

### 3. Chrome に読み込む

1. Chrome で新しいタブを開き、アドレスバーに `chrome://extensions` と入力して Enter を押します。  
   メニューから開く場合は、右上のその他アイコン（点が縦に3つ）→ **拡張機能** → **拡張機能を管理** です。
2. 画面右上の **デベロッパー モード** をオンにします。
3. 左上に出る **パッケージ化されていない拡張機能を読み込む** を押します。
4. 解凍した **asiandocs-1080p** フォルダ（`manifest.json` が直接入っているフォルダ）を選びます。

読み込めると、一覧に **Asiandocs 1080p** のカードが追加され、「拡張機能を読み込みました」と出ます。

### 4. 動いているか確かめる

1. 会員ページで動画を再生します。すでに開いていたページは、一度読み込み直してから再生してください。
2. 画質の表示が **1080p** になっていれば成功です。その動画に 1080p が無い場合は、自動以外で一番高い画質になっていれば成功です。
3. `chrome://extensions` に戻り、**Asiandocs 1080p** のカードが出ていて、右端のスイッチがオンになっていれば、拡張機能自体は有効です。

### 5. 更新する

1. インストールの先頭と同じリンクから ZIP をもう一度ダウンロードして解凍します。
2. 今 Chrome に読み込ませている **asiandocs-1080p** フォルダの中身を、新しい ZIP の中身で入れ替えます。フォルダの場所は変えないでください。
3. `chrome://extensions` を開きます。
4. **Asiandocs 1080p** のカードにある丸い矢印のボタンを押します。マウスを乗せると **再読み込み** と出ます。終わると「再読み込みされました」と出ます。
5. 見ている動画のページも、一度読み込み直します。

### 6. 削除する（アンインストール）

`chrome://extensions` で **Asiandocs 1080p** のカードの **削除** を押します。確認でも **削除** を押すと外れます。

Chrome から削除したあとも、パソコンに残った解凍フォルダは手動で捨てて構いません。

## よくあるつまずき

**フォルダが違う**

`manifest.json` が直接見えない、ひとつ外側のフォルダを選ぶと、「拡張機能を読み込めませんでした」「マニフェストを読み込めませんでした。」と出ます。解凍してできた `asiandocs-1080p`（`manifest.json` が直接入っているフォルダ）を選び直してください。

**デベロッパー モードがオフ**

**パッケージ化されていない拡張機能を読み込む** は、右上の **デベロッパー モード** がオンのときだけ出ます。オフにすると、この拡張機能は無効になります。カードには「この拡張機能を使用するには、デベロッパー モードをオンにしてください。この拡張機能は Chrome ウェブストアの審査を受けることができません。」と出ます。画面には「デベロッパー モードがオフです。一部の拡張機能は無効になっています。」と出ることもあります。Chrome を起動したときにこの表示が出ても、故障ではありません。ストアを通さずフォルダから読み込んだ拡張機能への注意です。**デベロッパー モード** をオンに戻すと、また使えます。

**カードのスイッチがオフ**

一覧にカードがあっても、右端のスイッチがオフだと動きません。スイッチをオンにしてください。

**ページを開き直していない**

拡張機能を入れたとき、更新したとき、画質が切り替わらないときは、動画のページを再読み込みしてから再生し直してください。すでに開いていたページには、読み込み直すまで入りません。

**解凍したフォルダを動かした、または消した**

Chrome は、読み込んだときのフォルダを見にいって動きます。インストール後にそのフォルダを削除したり移動したりしないでください。

### それでも動かないとき

次のことを知らせてください。個人のページアドレスやログイン情報は不要です。

- 選んだフォルダの名前と、その中に `manifest.json` が直接あったか
- **デベロッパー モード** がオンか
- カードのスイッチがオンか
- Chrome が出した文言（「マニフェストを読み込めませんでした。」など）
- 再生中の画質表示（360p のまま、自動、など）
- 動画のページを再読み込みしたか

## 権限

この拡張機能が入るサイトは、次の4つだけです。

- `asiandocs.co.jp`
- `asiandocs.co.jp` のサブドメイン（`*.asiandocs.co.jp`）
- `stream.ne.jp`
- `stream.ne.jp` のサブドメイン（`*.stream.ne.jp`）

`stream.ne.jp` は、会員ページの中で動く再生プレーヤーの側です。それ以外のサイトには入りません。

Cookie を読む権限も、開いているタブ一覧を見る権限もありません。通信もしません。画質の表示を見てボタンを押すだけです。入力した内容や視聴の記録を集めたり、どこかへ送ったりはしません。

## English

This Chrome extension switches the player on Asiandocs member pages to 1080p. If 1080p is not listed, it selects the highest available quality and never selects Auto. It only clicks the quality control on the page. It does not use the cookies or tabs permissions, does not make network requests, and does not collect data. It runs only on `asiandocs.co.jp`, `*.asiandocs.co.jp`, `stream.ne.jp`, and `*.stream.ne.jp`. Switching to 1080p was confirmed on a real member page.

### Install

https://github.com/souljazzfunk/lab/releases/download/asiandocs-1080p-latest/asiandocs-1080p.zip

1. Open the link above and download `asiandocs-1080p.zip`. This zip is the extension only, not the whole repository.
2. Unzip it. You get one `asiandocs-1080p` folder, with `manifest.json` directly inside.
3. Open `chrome://extensions`.
4. Turn on **Developer mode**.
5. Click **Load unpacked** and choose that unzipped `asiandocs-1080p` folder. Choose the folder that contains `manifest.json` directly. A parent folder makes Chrome report that it could not load the manifest.
6. Leave the unzipped folder where it is. Moving or deleting it stops the extension.
7. Open a member video page and start playback. Reload the page if it was already open. The quality should move to 1080p, or to the highest listed quality when 1080p is absent.

### Update

1. Download the ZIP again from the same link and unzip it.
2. Replace the files inside the `asiandocs-1080p` folder Chrome is already loading. Do not move that folder.
3. On `chrome://extensions`, click the reload button on the Asiandocs 1080p card (the tooltip says **Reload**).
4. Reload the video page.

### Uninstall

On `chrome://extensions`, click **Remove** on the Asiandocs 1080p card, then confirm. You can delete the unzipped folder after that.
