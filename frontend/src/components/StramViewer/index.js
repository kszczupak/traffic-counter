import React, {Component} from 'react';
import './index.css';

class StreamViewer extends Component {
 	constructor(props) {
 		super(props);

 		this.videoRef = null;
 	}


 	setVideoRef = element => {
 		this.videoRef = element;
 	};


	componentDidMount() {    
        const mimeCodec = 'video/mp4; codecs="avc1.640028"';

        var myMediaSource = new MediaSource();
 		const url = URL.createObjectURL(myMediaSource);
 		
 		this.videoRef.src = url;

 		myMediaSource.addEventListener('sourceopen', sourceOpenHandler);


 		function sourceOpenHandler(){
 			const videoSourceBuffer = myMediaSource.addSourceBuffer(mimeCodec);
 			// videoSourceBuffer.mode = 'sequence';

	 		var chunkUrls = [
	 			"http://localhost:8085/video/seg_1.mp4",
	 			"http://localhost:8085/video/seg_2.mp4",
	 			"http://localhost:8085/video/seg_3.mp4"
	 		];


 			videoSourceBuffer.addEventListener('updateend', readNextChunk);

	 		readNextChunk();

	 		function readNextChunk() {
	 			if (!chunkUrls.length) {
	 				// No segments left - this means that end of the stream is reached
	 				myMediaSource.endOfStream();
	 				return;
	 			}
	 			const currentVideoUrl = chunkUrls.shift();
	 			console.log(currentVideoUrl);

	 			fetch(currentVideoUrl)
	 				.then(response => {
	 					return response.arrayBuffer();
	 				})
	 				.then(videoData => {
	 					if (videoSourceBuffer.buffered.length) {
	 						// Offset segments 1 and above (offset of the segment_0 = 0 by default)
	 						videoSourceBuffer.timestampOffset = videoSourceBuffer.buffered.end(0);
	 					}

						videoSourceBuffer.appendBuffer(videoData);
	 				});
 			};
 		};
    }

	render() {
  		return (
		    <div>
		    	<video ref={this.setVideoRef} controls width="800"/>
		    </div>  
  		);
  	}
}

export default StreamViewer;
