import React, { useState } from 'react';

const video_processor: React.FC = () => {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [outputFolder, setOutputFolder] = useState<string>('');
  const [processing, setProcessing] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string>('');

  const handleVideoFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setVideoFile(event.target.files[0]);
    }
  };

  const handleOutputFolderChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setOutputFolder(event.target.value);
  };

  const handleStartProcessing = async () => {
    if (!videoFile) {
      setErrorMessage('動画ファイルを選択してください。');
      return;
    }
    if (!outputFolder) {
      setErrorMessage('出力フォルダを選択してください。');
      return;
    }

    setProcessing(true);
    setProgress(0);
    setErrorMessage('');

    // ここに動画処理のロジックを実装
    // (OpenCVを使った処理、フレームレート変換、フレーム抽出、ファイル保存など)
    // ダミーの処理を記述
    let currentProgress = 0;
    const interval = setInterval(() => {
      currentProgress += 10;
      setProgress(currentProgress);
      if (currentProgress >= 100) {
        clearInterval(interval);
        setProcessing(false);
        alert('動画処理が完了しました！');
      }
    }, 500);
  };

  return (
    <div className="flex justify-center items-start min-h-screen bg-white dark:bg-gray-800 pt-10">
      <Card className="w-3/4 max-w-2xl bg-card">
        <CardHeader className="bg-card">
          <CardTitle className="text-center">動画処理とフレーム抽出</CardTitle>
          <CardDescription className="bg-card">
            動画ファイルからフレームを抽出し、指定されたフォルダに保存します。
          </CardDescription>
        </CardHeader>
        <CardContent className="bg-card">
          {errorMessage && (
            <div className="mb-4 text-red-500">{errorMessage}</div>
          )}

          <div className="mb-4">
            <Label htmlFor="videoFile">動画ファイルを選択:</Label>
            <Input type="file" id="videoFile" accept=".mp4,.avi" onChange={handleVideoFileChange} />
          </div>

          <div className="mb-4">
            <Label htmlFor="outputFolder">出力フォルダ:</Label>
            <Input type="text" id="outputFolder" value={outputFolder} onChange={handleOutputFolderChange} placeholder="出力フォルダのパスを入力" />
          </div>

          <Button onClick={handleStartProcessing} disabled={processing}>
            {processing ? '処理中...' : '処理開始'}
          </Button>

          {processing && (
            <div className="mt-4">
              <Label>進捗: {progress}%</Label>
              <progress value={progress} max="100" className="w-full"></progress>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default video_processor;