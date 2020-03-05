import React, {Component} from 'react';
import './index.css';

class StreamViewer extends Component {
 	constructor(props) {
 		super(props);

 		this.videoRef = null;
 		this.videoSourceBuffer = null;
 		this.segmentDownloadingInProgress = false;
 		this.segmentsQueue = [];
 		this.eventSource = null;
 	}


 	setVideoRef = element => {
 		this.videoRef = element;
 	};

 	fetchNextSegment = () => {
 		if (!this.segmentsQueue.length) {
 			this.segmentDownloadingInProgress = false;
 			return;
 		}

 		this.segmentDownloadingInProgress = true;
 		const segmentUrl = this.segmentsQueue.shift()

		fetch(segmentUrl)
		.then(response => {
			return response.arrayBuffer();
		})
		.then(videoData => {
			if (this.videoSourceBuffer.buffered.length) {
				// Offset segments 1 and above (offset of the segment_0 = 0 by default)
				this.videoSourceBuffer.timestampOffset = this.videoSourceBuffer.buffered.end(0);
			}

		this.videoSourceBuffer.appendBuffer(videoData);
		});
 	};


	componentDidMount = () => {    
        const mimeCodec = 'video/mp4; codecs="avc1.640028"';

        var myMediaSource = new MediaSource();
 		const url = URL.createObjectURL(myMediaSource);
 		
 		this.videoRef.src = url;


 		const sourceOpenHandler = () => {
 			this.videoSourceBuffer = myMediaSource.addSourceBuffer(mimeCodec);
 			// videoSourceBuffer.mode = 'sequence';

 			this.videoSourceBuffer.addEventListener('updateend', this.fetchNextSegment);

 			this.source = new EventSource("http://192.168.0.177:5001/ready_segments_stream");

	 		this.source.onopen = () => {
	 			console.log("Source stream opened");

	 		};

	 		this.source.onmessage = event => {

	 			const readySegment = JSON.parse(event.data).segment_path;
	 			const readySegmentUrl = "http://localhost:8085/" + readySegment;
	 			console.log(readySegmentUrl);

	 			this.segmentsQueue.push(readySegmentUrl);

	 			if (!this.segmentDownloadingInProgress) {
	 				this.fetchNextSegment();
	 			}
	 		};
 		};

 		myMediaSource.addEventListener('sourceopen', sourceOpenHandler);
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
